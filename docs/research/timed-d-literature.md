# Research decisions for the 30-minute D round

Sources checked on 8 November 2026, before the new round's completed test
comparisons. These are established methods; adapting them is sufficient for a
course project but does not establish a new statistical contribution.

| Primary source | Relevant idea | Project decision and boundary |
| --- | --- | --- |
| [Angelopoulos, Duchi & Zrnic, PPI++](https://arxiv.org/html/2311.01453v2), sections 2.2/6 | Weight prediction correction to adapt to prediction quality | Test a fixed five-weight grid, chosen on validation before test. Our fixed finite population, unequal allocation and development transfer differ from the paper's iid setup; its efficiency claims are not inherited |
| [Dagdoug, Goga & Haziza, model-assisted estimation](https://arxiv.org/abs/2012.07385) | Survey estimation can use auxiliary predictions; penalized and tree models have different efficiency | Supports retaining simple controls and reporting learners that lose. Their model is fitted on sampled survey observations; our frozen development-trained functions have a different training boundary |
| [Barcaroli, SamplingStrata](https://www.jstatsoft.org/article/view/v061i04) | Stratification and allocation jointly affect precision under a budget | Use a small registered quantile-strata grid. We do not implement or claim to reproduce its genetic optimization or multi-domain cost guarantees |

The working hypothesis is that more useful allocation may matter more than a
more complex temporal learner. Earlier results motivate that hypothesis but do
not prove it. D2 is selected on three validation sources, so a win or loss can
reflect transfer mismatch. The test corpus has been repeatedly inspected;
additional draws reduce Monte Carlo error, not that development bias.

The next scientifically stronger step after this timebox would be evaluation
on genuinely unseen source videos with a frozen recipe. Expanding the same
test-driven candidate search is weaker evidence. This is a recommendation for
future work, not a newly authorized data collection or another registered grid.
