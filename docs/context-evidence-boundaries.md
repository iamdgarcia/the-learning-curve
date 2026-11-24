# Preserve an observation without mistaking it for current state

**Scope:** a design note based on the historical `contributor-lab` research prototype, not a new package release or an installed agent integration.

`contributor-lab` was removed from the repository in commit [`6053ce2`](https://github.com/iamdgarcia/the-learning-curve/commit/6053ce2b9b2adbbd408d06445312c0a35876c757). It is absent from current `main`. The source discussed here is pinned to [`dbb7e83`](https://github.com/iamdgarcia/the-learning-curve/tree/dbb7e83bef388ef73082a0ea857515facb0610f9/contributor-lab), the last revision before removal. This note does not restore the deleted package.

An agent can keep a tool result in an archive without putting the entire result into every model request. But recovering the original observation and proving the external state are different jobs.

## Three questions, three checks

- **What did the tool return then?** Retrieve the archived observation with its provenance.
- **Does the archived file still match its identifier?** Check integrity separately; a hash-shaped filename does not perform that check.
- **Is the external record correct now?** Read the exact target again when current state is required.

A model-generated summary cannot replace the first check. A recovered historical response cannot replace the third. A trustworthy integration needs to preserve the distinction even when all three return similar-looking text.

## What the historical `ArtifactStore` actually implements

The implementation is in [`bounded_context.py`](https://github.com/iamdgarcia/the-learning-curve/blob/dbb7e83bef388ef73082a0ea857515facb0610f9/contributor-lab/bounded_context.py#L133-L151).

`save(text)` hashes `text.encode()` using SHA-256. The default string encoding for this operation is UTF-8. It uses the lowercase hexadecimal digest as the identifier and writes a `.txt` file only if that path does not already exist. Saving the same string returns the same identifier.

`read(identifier, start=0, end=None)` accepts a 64-character lowercase hexadecimal identifier. It rejects a negative start or an end before the start. It reads the entire text file and then applies a Python string slice.

Consequences worth keeping explicit:

- The offsets are character indices, not byte offsets or model tokens. `start` is inclusive and `end` is exclusive.
- Omitting `end` returns the remaining string. An out-of-range start can return an empty string instead of raising an error.
- A small returned slice does not mean bounded disk I/O or a bounded whole-file allocation.
- The reader does not recompute the digest. Modifying the file can change the returned text without changing the identifier.
- `save` does not repair a modified file at an existing identifier.
- The implementation does not enforce filesystem immutability or atomic concurrent publication. Its docstring's word “immutable” is an intention, not an enforced storage property.
- Disk operations use `Path.write_text` and `Path.read_text` without an explicit encoding. The identifier hashes UTF-8 input, but this is not a raw HTTP-byte recorder or a cross-platform guarantee about stored byte representation. Preserve raw bytes separately when byte identity matters.

No production storage guarantee should be inferred from a Unicode round-trip unit test.

## A concrete distinction

Suppose a tool response says that record `r-0042` has status `done`. Archiving it lets another step recover exactly what was reported.

It does not establish that the response came from an authorized write, that the tool targeted the intended account, or that the record still has that value. If completion requires current state, query `r-0042` in the intended account and compare that observation against the acceptance criterion.

An unresolved write needs reconciliation, not a confident summary or a blind retry. A later matching record value can verify current state, but it does not retroactively establish permission for a past action.

## What an integration would need beside the text

The following is a proposed integration record, **not an implemented `ArtifactStore` schema**:

```json
{
  "artifact_id": "<digest returned by the store>",
  "tool": "read_record",
  "arguments": {"record_id": "r-0042"},
  "target": {"account_id": "example-account", "record_id": "r-0042"},
  "observed_at": "<timestamp of the actual observation>",
  "execution_status": "succeeded",
  "integrity_checked": false,
  "freshness": "historical_observation"
}
```

Keep permissions in a separately enforced policy, not in text selected by a relevance model. Minimize and protect archived arguments/results that contain personal data or secrets; do not publish operational traces merely because they are easy to hash.

The working model context can carry the task, mandatory constraints and a precise evidence reference. Expand the passage when the decision needs it. A pointer alone does not prove the model retrieved or understood its contents.

## Reproduce the historical unit suite without restoring `main`

From a clone of this repository, use a detached worktree at the pinned historical revision:

```bash
git worktree add --detach ../tlc-lab-history dbb7e83bef388ef73082a0ea857515facb0610f9
cd ../tlc-lab-history/contributor-lab
python -m unittest -v test_bounded_context
```

Choose an unused worktree path. The command is for a checkout that has the pinned revision available; it does not change the branch in the main working directory. Python 3.10 or later and the standard library are sufficient for this suite. It does not require a model server or API credential.

**Rechecked on 24 November 2026:** all 17 historical unit tests passed at the pinned revision. Separate isolated checks also confirmed character slicing, invalid-range rejection, empty out-of-range reads, retrieval of externally modified content without a hash check, and the fact that saving the original text again does not repair that modified file.

These observations describe the pinned historical implementation. They are not tests of the current `main` package: that package is no longer present.

## What this execution does not establish

The suite uses `DeterministicTestCounter`, a deliberately byte-based test double, not a model tokenizer. It checks context/compiler invariants and a simplified `VerifiedState` completion gate.

It does not establish production transaction safety, archive concurrency or tamper detection, reliable downstream evidence retrieval, model task success, calibrated confidence, or accepted-task cost savings. No inference diagnostics or external record mutations were run for this documentation update.

The useful design principle survives the prototype: **preserve evidence, check integrity, and verify current state as separate responsibilities.**

Follow the ongoing experiments in [The Learning Curve](https://iamdgarcia.substack.com).
