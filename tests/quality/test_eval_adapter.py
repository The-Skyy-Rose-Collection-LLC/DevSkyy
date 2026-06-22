from evaluation.adapter import DomainAdapter


def test_protocol_runtime_checkable():
    class Dummy:
        domain = "x"

        def deterministic_checks(self, subject, ref):
            return []

        def build_judge_request(self, subject, ref):
            return {}

        def parse_verdict(self, judge_output, det_failures): ...
        async def revise(self, ref, critique): ...
        def load_ground_truth(self):
            return []

    assert isinstance(Dummy(), DomainAdapter)
