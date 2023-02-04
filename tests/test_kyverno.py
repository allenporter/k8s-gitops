"""Tests that run `kyverno test`.

Tests here are used to test the policies themselves, and not actually applying
policies to cluster resources. That is done in other tests for the specific
resources.

See https://kyverno.io/docs/kyverno-cli/#test for details on how to write
policy tests.

See `infrastructure/base/policies/` for the actual policies.
"""

from scripts.manifest import cmd


POLICY_TEST_DIR = "tests/policies"


async def test_policies() -> None:
    """Run tests against the policies themselves."""
    await cmd.run_command(
        [
            "kyverno",
            "test",
            POLICY_TEST_DIR,
        ],
    )
