# Course results assessment through G2

The project is a reproducible system for estimating benchmark-defined
mutual-looking prevalence from a frozen gaze cache and limited random reference
queries. Its course contribution is a working audit pipeline, honest controls,
cost/uncertainty diagnostics and an inspectable replay. It does not require a new
statistical theorem, and it is not an ADHD diagnostic or clinical gaze measure.

The useful extension is validation-selected prediction weighting. At the10%
audit budget, D's same-query score-stratum comparison reduces RMSE0.219884 to
0.196725 pp, ratio0.894677 [0.871237,0.919003]. The original B1 stream7 control
was0.207857 pp; the same-query effect uses D stream21, not a changed dataset.
This remains exploratory after repeated inspection of the same test corpus.

The gain is heterogeneous. Three of six positive-reference sources improve,
three lose. Four zero-positive sources halve their errors mechanically under
lambda0.5. All ten leave-one-source-out aggregates improve, but omitting one
influential source reduces the gain to about1.2%, with uncertainty including a
tie. This is sensitivity on overlapping domains, not unseen-source validation.

The original primary temporal-versus-static comparison does not show a clear
temporal gain. Shorter-window and feature-removal checks, alternate learners,
and block guidance do not justify replacing that result. In G2's L5/B1032
primary comparison, temporal RMSE0.59810 exceeds static0.53696 pp: ratio1.11386
[1.03890,1.20339]. Native score guidance is better than both there (0.47406),
and G2 L1 native-score guidance is better still. Keep every loss in the appendix.

Contiguous blocks reduce query-task counts but lose precision at matched
expected label cost. Uniform L5 versus L1 has RMSE ratio2.10893 atB1032.
Guidance recovers much of that loss relative to uniform blocks, without showing
a long-block accuracy advantage over frame queries. Actual block label costs
vary and sometimes exceed the nominal expected budget. No actual human effort
or timing study has been performed.

The C2 downstream-label curve is useful for a course discussion:9599 training
labels give RMSE0.2120 pp versus0.2148 with191956 on its registered common
stream. Every point also reuses25139 validation labels and the pretrained gaze
backbone. It is not evidence of annotation-free learning or total cold-start cost.

Interval reliability is unresolved. Weighting improves the point estimator but
its normal coverage at40% is only39.1%. Separate conservative binary references
and public error weighting retain fixed-design coverage under their assumptions,
but remain broad; the primary weighted-width improvement is only2.59%. Block
residual totals use a different conservative bounded construction. Do not clip
the point into a reference interval or replace original failing error bars.

The strongest next scientific evidence would come from a genuinely unseen,
properly aligned source evaluation with the recipe frozen. The current media
population retains53 of95 attempted sources, including40 train,3 validation,
10 test. Existing excluded/misaligned or previously summarized sources must not
silently become a new independent benchmark. Availability and prior inspection
must be audited before a new evaluation is registered.

## Full appendices

- [Original course report](../reports/course-project/course-report.md)
- [Strengthening and exact-reference diagnostics](../reports/course-project/strengthening-report.md)
- [C: learners and label cost](../reports/course-project/extra-c/results.md)
- [D: fixed prediction weighting](../reports/course-project/timed-d/results.md)
- [E: source sensitivity](../reports/course-project/source-e/results.md)
- [F: public error-weight intervals](../reports/course-project/weighted-f/results.md)
- [G1: uniform contiguous blocks](../reports/course-project/block-g/results.md)
- [G2: frozen block guidance](../reports/course-project/block-guidance-g2/results.md)
- [Research explorer walkthrough](RESEARCH_EXPLORER_GUIDE.md)
