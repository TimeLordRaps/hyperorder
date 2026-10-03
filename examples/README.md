# Retained paired examples

`paired-frame.json` records both colorings, every continuation rule and
both invariant sets. `divergence-families.json` contains two distinct
branching families. `escape-frame.json` adds an unresolved alternative;
its favorable converging path still exists, but universal convergence fails.

```console
python -B -u hyperorder.py converge examples/paired-frame.json examples/divergence-families.json paired-form
python -B -u hyperorder.py converge examples/escape-frame.json examples/divergence-families.json paired-form
```

The first command exits 0 with PASS. The second exits 1 with FAIL and names
the affected family member. These files are [FRAME] research inputs, not
records of physical measurements or native □-formation certificates.

The same paired example is embedded in the installable package's `demo`
operation, so an installed wheel needs no source-tree fixtures to run.
