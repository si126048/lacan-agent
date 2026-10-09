from __future__ import annotations
import logging
from .db import Store, new_id
from .models import (
    AnalysisRun, AnalysisPacket, RunState, ReviewStatus, ReviewDecision,
    ReviewRequest, EvidenceSpan, Observation, Hypothesis,
    GraphNode, GraphEdge, NarrativeOperator,
)
from .llm import FakeProvider, EVIDENCE_SYSTEM, INTERPRETER_SYSTEM, CRITIC_SYSTEM
from .rag import validate_span
from .fuzzy import MembershipFunction, aggregate_grounding, HallucinationGuard, FuzzyGrounding
from .annotation import CulturalAnnotator

logger = logging.getLogger(__name__)


class Workflow:
    def __init__(self, store: Store, provider=None):
        self.store = store
        self.provider = provider or FakeProvider()

    def _set(self, r: AnalysisRun, state: RunState, reason: str, actor: str = 'system') -> None:
        r.state = state
        self.store.audit(r, actor, reason)
        logger.info("run=%s state=%s reason=%s", r.id, state, reason)

    def run(self, project_id: str, participant_id: str, source_ids: list[str], idem: str) -> AnalysisRun:
        existing = self.store.get_run_by_idem(project_id, idem)
        if existing:
            return existing

        p = self.store.get_participant(project_id, participant_id)
        if not p or p.withdrawn_at or not p.consent_scope.research_analysis:
            raise PermissionError('CONSENT_REQUIRED')

        docs = [self.store.get_document(x) for x in source_ids]
        if any(not d or d.participant_id != participant_id or d.project_id != project_id for d in docs):
            raise PermissionError('OBJECT_ACCESS_DENIED')

        r = AnalysisRun(
            id=new_id('run'), project_id=project_id, participant_id=participant_id,
            source_ids=source_ids, state=RunState.CREATED, idempotency_key=idem,
        )
        self.store.put_run(r)
        self._set(r, RunState.INGESTED, 'audit complete')

        spans = self._collect_evidence(docs)
        obs = self._observe(r, spans)
        annotations = self._annotate(spans)
        hyps = self._interpret(r, obs, project_id, annotations)
        hyps = self._critique(r, obs, hyps)
        return self._finalize(r, participant_id, obs, hyps, spans, annotations)

    def _collect_evidence(self, docs: list) -> list[EvidenceSpan]:
        spans: list[EvidenceSpan] = []
        for d in docs:
            spans.extend(self.store.list_spans_for_document(d.id))
        valid = [s for s in spans if validate_span(self.store, s.id)]
        logger.debug("evidence: %d total spans, %d valid", len(spans), len(valid))
        return valid

    def _observe(self, r: AnalysisRun, spans: list[EvidenceSpan]) -> list[Observation]:
        sample = spans[:50]
        spans_text = '\n\n'.join(f'[span_id={s.id}]\n{s.excerpt}' for s in sample)
        ev = self.provider.generate_structured(
            EVIDENCE_SYSTEM,
            {'span_ids': [s.id for s in spans], 'spans_text': spans_text},
            Observation, {'stage': 'evidence'},
        )
        obs = [Observation.model_validate(x) for x in ev['observations']]
        self._set(r, RunState.OBSERVED, 'evidence spans validated')
        logger.info("observations: %d", len(obs))
        return obs

    def _annotate(self, spans: list[EvidenceSpan]) -> list:
        try:
            annotator = CulturalAnnotator()
            return annotator.annotate(spans)
        except Exception:
            logger.warning("cultural annotation failed, continuing without annotations")
            return []

    def _interpret(self, r: AnalysisRun, obs: list[Observation], project_id: str,
                   annotations: list | None = None) -> list[Hypothesis]:
        theory_spans = self.store.list_theory_spans(project_id)
        theory_refs = [s.id for s in theory_spans]
        theory_text = '\n'.join(s.excerpt for s in theory_spans)
        annotation_context = ""
        if annotations:
            annotation_context = "\n".join(
                f"[{a.entity_name}] ({a.entity_type}): {a.context_brief}"
                for a in annotations
            )
        hyp = self.provider.generate_structured(
            INTERPRETER_SYSTEM,
            {
                'observation_ids': [o.id for o in obs],
                'theory_reference_ids': theory_refs,
                'observation_labels': [o.label for o in obs],
                'theory_text': theory_text,
                'cultural_annotations': annotation_context,
            },
            Hypothesis, {'stage': 'interpreter'},
        )
        hyps = [Hypothesis.model_validate(x) for x in hyp['hypotheses']]
        self._set(r, RunState.INTERPRETED, 'structured hypotheses generated')
        logger.info("hypotheses: %d", len(hyps))
        return hyps

    def _critique(self, r: AnalysisRun, obs: list[Observation], hyps: list[Hypothesis]) -> list[Hypothesis]:
        hyps_summary = [{'id': h.id, 'concept_ids': h.concept_ids, 'alternatives': h.alternatives} for h in hyps]
        crit = self.provider.generate_structured(
            CRITIC_SYSTEM,
            {
                'observation_ids': [o.id for o in obs],
                'observation_labels': [o.label for o in obs],
                'hypotheses_summary': hyps_summary,
                'hypothesis_ids': [h.id for h in hyps],
            },
            dict, {'stage': 'critic'},
        )
        crit_by_hyp = crit.get('counterexamples_by_hypothesis', {})
        for h in hyps:
            h.counterexamples.extend(crit_by_hyp.get(h.id, crit.get('counterexamples', [])))
        r.topology['critic_disconfirmation'] = crit.get('fuzzy_disconfirmation_by_hypothesis', {})
        r.topology['critic_grounding'] = crit.get('grounding_assessment_by_hypothesis', {})
        r.topology['critic_ungrounded'] = crit.get('ungrounded_claims_by_hypothesis', {})
        self._set(r, RunState.CRITIQUED, 'independent counterexample pass complete')
        return hyps

    def _finalize(self, r: AnalysisRun, participant_id: str, obs: list[Observation],
                  hyps: list[Hypothesis], spans: list[EvidenceSpan],
                  annotations: list | None = None) -> AnalysisRun:
        mf = MembershipFunction()
        guard = HallucinationGuard()
        hallucination_reports = []

        for h in hyps:
            groundings = [mf.compute(h, s, obs) for s in spans if s.id in h.support_ids]
            counter_groundings = [mf.compute(h, s, obs) for s in spans if s.id in h.counterexamples]
            h.grounding_score = aggregate_grounding(groundings, counter_groundings)
            h.fuzzy_groundings = [
                {"span_id": g.evidence_span_id, "membership": g.membership, "components": g.components}
                for g in groundings
            ]
            report = guard.check(h, groundings)
            hallucination_reports.append(report.to_dict())
            if report.risk_level == "high":
                h.status = ReviewStatus.NEEDS_REVISION
                logger.warning("hypothesis %s flagged high hallucination risk (score=%.3f)", h.id, h.grounding_score)

        packet = AnalysisPacket(
            run_id=r.id, participant_id=participant_id,
            state=RunState.NEEDS_HUMAN_REVIEW, observations=obs, hypotheses=hyps,
            hallucination_reports=hallucination_reports,
            cultural_annotations=annotations or [],
        )
        r.packet = packet
        self._set(r, RunState.NEEDS_HUMAN_REVIEW, 'awaiting human review')
        return r

    def review(self, rid: str, req: ReviewRequest) -> AnalysisRun:
        r = self.store.get_run(rid)
        if not r:
            raise KeyError('RUN_NOT_FOUND')
        if r.state != RunState.NEEDS_HUMAN_REVIEW:
            raise ValueError('INVALID_REVIEW_STATE')
        if req.decision == ReviewDecision.APPROVE:
            r.state = RunState.APPROVED
            r.packet.state = RunState.APPROVED
            for h in r.packet.hypotheses:
                h.status = ReviewStatus.APPROVED
        elif req.decision == ReviewDecision.REVISE:
            r.state = RunState.REVISION_REQUIRED
            r.packet.state = RunState.REVISION_REQUIRED
        else:
            r.state = RunState.FAILED
            r.packet.state = RunState.FAILED
            r.packet.errors.append(req.reason or 'rejected')
        self.store.audit(r, req.reviewer_id, req.reason or req.decision.value)
        logger.info("review: run=%s decision=%s", rid, req.decision.value)
        return r

    def export(self, rid: str) -> dict:
        r = self.store.get_run(rid)
        if not r:
            raise KeyError('RUN_NOT_FOUND')
        if r.state not in (RunState.APPROVED, RunState.COMPILED):
            raise PermissionError('NOT_APPROVED')
        p = self.store.get_participant(r.project_id, r.participant_id)
        if not p or not p.consent_scope.generation:
            raise PermissionError('GENERATION_NOT_CONSENTED')
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        ops: list[NarrativeOperator] = []
        obs_by_id = {o.id: o for o in r.packet.observations}
        for o in r.packet.observations:
            nodes.append(GraphNode(id=o.id, type='signifier', label=o.label, source_ids=o.evidence_span_ids, status='approved'))
        discourse_trajectory = []
        for h in r.packet.hypotheses:
            nodes.append(GraphNode(id=h.id, type='interpretation', label=h.id, source_ids=h.support_ids, status='approved'))
            if h.discourse_type:
                discourse_trajectory.append(h.discourse_type)
            for mid in h.matheme_ids:
                nodes.append(GraphNode(id=mid, type='matheme', label=mid, status='approved'))
                edges.append(GraphEdge(id=new_id('edge'), source=mid, target=h.id, type='matheme', evidence_span_ids=[]))
            for pc in h.points_de_capiton:
                nodes.append(GraphNode(id=pc.id, type='capiton_point', label=pc.signifier, source_ids=pc.fixation_span_ids, status='approved'))
                edges.append(GraphEdge(id=new_id('edge'), source=pc.id, target=h.id, type='capiton', evidence_span_ids=pc.fixation_span_ids))
            for sid in h.support_ids:
                evidence = obs_by_id.get(sid).evidence_span_ids if obs_by_id.get(sid) else []
                if evidence:
                    edges.append(GraphEdge(id=new_id('edge'), source=sid, target=h.id, type='hypothesis', evidence_span_ids=evidence))
            ops.append(NarrativeOperator(
                id=new_id('op'), operator='REPETITION', source_finding_ids=[h.id],
                allowed=True, use_cases=['在有跨情境证据时重现叙事关系'],
                counterexamples=h.counterexamples, approval_state='approved',
            ))
        prev_disc = None
        for dt in discourse_trajectory:
            if prev_disc and prev_disc != dt:
                edges.append(GraphEdge(id=new_id('edge'), source=prev_disc, target=dt, type='discourse_rotation', evidence_span_ids=[]))
            prev_disc = dt
        r.packet.narrative_operators = ops
        r.state = RunState.COMPILED
        r.packet.state = RunState.COMPILED
        self.store.put_run(r)
        logger.info("export: run=%s compiled", rid)
        topology = dict(r.topology)
        topology['discourse_trajectory'] = discourse_trajectory
        topology['capiton_points'] = [
            pc.model_dump() for h in r.packet.hypotheses for pc in h.points_de_capiton
        ]
        return {
            'run_id': rid,
            'packet': r.packet.model_dump(mode='json'),
            'graph': {'nodes': [n.model_dump() for n in nodes], 'edges': [e.model_dump() for e in edges]},
            'topology': topology,
            'annotations': [a.model_dump(mode='json') for a in r.packet.cultural_annotations],
            'hallucination_reports': r.packet.hallucination_reports,
        }
