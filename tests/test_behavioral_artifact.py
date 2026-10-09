import json
from pathlib import Path

import pytest

from lacan_agent.behavioral import BehavioralProfiler, ConsentPolicy
from lacan_agent.behavioral.chat_parser import load_participant_messages, load_normalized_messages
from lacan_agent.behavioral.config import load_participant_manifest
from lacan_agent.behavioral.inference import infer_claims


def test_profile_artifact_has_manifest_and_no_raw_samples(tmp_path):
    (tmp_path / 'friend.txt').write_text('你好⏎\n哈哈！⏎\n', encoding='utf-8')
    profiler = BehavioralProfiler(tmp_path, participants={'friend': 'friend.txt'})
    artifact = profiler.build_artifact('friend')
    assert artifact.schema_version == '1.0'
    assert artifact.source_manifest[0].message_count == 2
    assert 'sample_lines' not in artifact.observed_style
    assert artifact.generation_policy['raw_text_in_prompt'] is False


def test_profile_consent_is_required(tmp_path):
    (tmp_path / 'friend.txt').write_text('hello', encoding='utf-8')
    profiler = BehavioralProfiler(
        tmp_path, participants={'friend': 'friend.txt'},
        consent=ConsentPolicy(profile_analysis=False),
    )
    with pytest.raises(PermissionError, match='PROFILE_CONSENT_REQUIRED'):
        profiler.build_artifact('friend')


def test_manifest_and_gb18030_input(tmp_path):
    source = tmp_path / 'friend.txt'
    source.write_bytes('你好\n'.encode('gb18030'))
    manifest = tmp_path / 'participants.json'
    manifest.write_text(json.dumps({'participants': [{'id': 'x', 'file': 'friend.txt'}]}), encoding='utf-8')
    assert load_participant_manifest(manifest) == {'x': 'friend.txt'}
    assert load_participant_messages(source) == ['你好']
    assert load_normalized_messages(source, 'source')[0]['message_id'].startswith('msg_')


class FakeInference:
    def generate_structured(self, *_args):
        return {'topics': [{'id': 'topic_1', 'text': '问候', 'evidence_span_ids': ['msg_bad'], 'confidence': 0.8, 'alternatives': ['礼貌用语']}], 'episodes': [], 'relationships': [], 'inferred_traits': []}


def test_inference_rejects_unknown_evidence():
    with pytest.raises(ValueError, match='INVALID_PROFILE_EVIDENCE'):
        infer_claims(FakeInference(), [{'message_id': 'msg_ok', 'content': '你好'}])
