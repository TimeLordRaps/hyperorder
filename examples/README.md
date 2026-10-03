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

`abstraction-escape-frame.json` keeps two selected routes with identical
paired reconciliation schemas. The right origin additionally has an escape
to another landing. This demonstrates the off-branch abstraction separately
from global concrete reproduction:

```console
python -B -u hyperorder.py quad examples/abstraction-escape-frame.json left-start right-start --left-route left-step --right-route right-step --projection exact --retrace
```

The selected schema and both original route recoveries PASS; complete
landing coincidence and global simulation FAIL. No native `==` promotion
is inferred. For stationary multiplicity, compare one `self-read` to
`self-read self-return self-read` in `paired-frame.json` using projection
`stationary` and then `exact`. Only the explicit stationary policy forgets
their run multiplicity; each retrace still requires its original route.
