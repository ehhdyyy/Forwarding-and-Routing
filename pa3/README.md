# CS 158A PA3 starter

Edit only `router.py`, `dv.py` and `answers.json`. Leave everything else as it is.

    python run.py scenarios/s0_warmup.json          run a scenario, write trace.txt
    python run.py scenarios/s1_longest_prefix.json --verbose
                                                    add '#' lines: table lookups, vectors received, final tables
    python run.py scenarios/s2_link_failure.json --dv-infinity none
                                                    run with the infinity cap switched off
    python run.py scenarios/s2_link_failure.json --debug
                                                    echo your log() calls to the screen (also written to debug.log)
    python verify.py                                check all public scenarios against golden/
    python verify.py step1 step2                    check Steps 1 and 2 only
    python verify.py s1_longest_prefix              check one scenario
    python ping.py scenarios/s4_net.json A 10.0.6.1 --at 30
    python ping.py scenarios/s4_net.json A 10.0.6.1 --at 30 --to 40   one ping per tick, one line each
    python traceroute.py scenarios/s4_net.json A 10.0.6.1 --at 30
    python make_submission.py --name "First Last"   check your files and build the zip to upload

Python 3.8 or newer. No packages to install. On Mac and Linux the command is often `python3`.

Folders: `engine/` (given), `scenarios/` (public scenarios), `golden/` (expected output for each),
`topologies/` (the network). The brief explains the trace format and each step.

`answers.json` is a JSON file. Edit it in a plain text editor, replace each `null` with your value, put text in
straight double quotes and numbers bare. `python -m json.tool answers.json` checks that the file is valid.
