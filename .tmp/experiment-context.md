# Shared experiment context

## Paths

```
CLI=.build/release/TurboFieldfareCLI
MODEL=scratch/gemma4.gturbo
CORPUS=.tmp/confidential-gemma4-comparison/corpus
RESULTS=.tmp/confidential-gemma4-comparison/knobs
PROMPT='Summarise the following course transcript faithfully and concisely:'
```

## Preflight (run before EVERY model invocation)

1. `pgrep -fl 'TurboFieldfareServer|TurboFieldfareMac|TurboFieldfareDecodeService|TurboFieldfareCLI'` must return nothing
2. `ollama ps` must show no loaded Ollama model before a TurboFieldfare measurement; an idle `ollama serve` daemon is allowed
3. `memory_pressure -Q` → free% > 40%
4. `swift --version` → 6.2+
5. Disk > 10 GB free on volume
6. `ls scratch/gemma4.gturbo/manifest.json` exists
7. One model process at a time

If `ollama ps` lists a model before a TurboFieldfare measurement, run `ollama stop <model>` and recheck `ollama ps`. Do not terminate an idle daemon.

## Default config (production)

temperature=0.2, top-k=64, top-p=0.95, repetition-penalty=1.0, max-context=4096,
expert-cache-slots=16, expert-cache-policy=lfu, prefill=on, prefill-chunk-tokens=128, rdadvise=off

## Gate limits

- **GATE G1** (speed): TF median on chunk 06 ≤ 65.5s (Ollama chunk 06 = 60.13s × 1.09). And RSS flat across repeats (no monotonic growth = no leak). And at least one knob shows observable effect.
- **GATE G2** (quality): output size ratio TF/Ollama ∈ [0.5, 2.0] on each test chunk, and human eyeball says output is coherent/faithful (not junk/repetition).

## Knobs to test (one at a time on chunk 06)

| Knob | Min | Default | Max |
|---|---|---|---|
| context | 4096 | 4096 | 65536 |
| expert-cache-slots | 16 | 16 | 32 (8 invalid for this model) |
| expert-cache-policy | lfu | lfu | lru |
| prefill | off | on | on (chunk tokens variation) |
| prefill-chunk-tokens | 32 | 128 | — (128 is max, tested vs 32/64) |
| rdadvise | off | off | adaptive (+ bounded/default) |

## Knob-effectiveness proof

For each knob, run min vs max (1 run each). An effect is proven if:
- slots: peak RSS shifts by ≥ 100 MiB between 16 and 32
- prefill on/off: wall time or prefill tok/s shifts noticeably
- rdadvise off vs adaptive: decode tok/s or wall shifts ≥ 5%
- policy lfu vs lru: decode tok/s shifts ≥ 3%
- prefill-chunk-tokens 32 vs 128: wall time shifts

If no clear signal: escalate to 3× repeats at min+max to filter noise.
If still no signal: record "inert on this workload" and exclude from optimization.

## Run template

```bash
# Preflight (always first)
memory_pressure -Q && ollama ps

# Warmup (discarded)
$CLI --model $MODEL --max-context 4096 --temperature 0.2 --top-k 64 --top-p 0.95 --repetition-penalty 1.0 --prompt "$PROMPT

$(cat $CORPUS/benchmark06.md)" > /dev/null

# Measure (capture timing + RSS)
/usr/bin/time -l $CLI --model $MODEL --max-context 4096 --temperature 0.2 --top-k 64 --top-p 0.95 --repetition-penalty 1.0 [KNOB FLAGS] --prompt "$PROMPT

$(cat $CORPUS/benchmark06.md)" > $RESULTS/run-NN/summary.md 2>$RESULTS/run-NN/stderr.txt
```

Extract from stderr footer: prefill=Ntok new=Ntok decode=X.XXs tok/s=Y.YYY
Extract from /usr/bin/time -l: "maximum resident set size" → RSS bytes.

## Unique output folders

Each measured run writes to `$RESULTS/<config-slug>/run-<NN>/` where NN starts at 01.
Config slug examples: `default`, `slots-32`, `prefill-off`, `rdadvise-adaptive`.

## Privacy

Never print chunk content, summary content, file paths containing confidential material, or API keys. All output captured into .tmp only.
