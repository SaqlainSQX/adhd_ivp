window.TRANSFER_DATA = {
  "version": 1,
  "scope": "aggregate course appendix; no raw labels or queries",
  "population": {
    "eligible_pairs": 5219,
    "test_clips": 15,
    "TV_shows": 4,
    "draws_per_method_budget": 1000,
    "total_validated_method_draws": 12000
  },
  "primary_budget": 521,
  "budgets": [
    260,
    521,
    1043,
    2087
  ],
  "uco": {
    "rows": [
      {
        "budget": 260,
        "method": "uniform",
        "rmse_pp": 1.163361456343179,
        "bias_pp": -0.041415430948320266,
        "mae_pp": 0.9193663610487278,
        "normal": {
          "coverage": 0.95,
          "mean_width_pp": 4.648610937666095,
          "median_width_pp": 4.643306236908658
        },
        "exact": {
          "coverage": 0.953,
          "mean_width_pp": 10.86058631921824
        }
      },
      {
        "budget": 260,
        "method": "K4",
        "rmse_pp": 0.9473302119257416,
        "bias_pp": 0.012490716621419231,
        "mae_pp": 0.741630596624397,
        "normal": {
          "coverage": 0.95,
          "mean_width_pp": 3.784928731113229,
          "median_width_pp": 3.782990775211907
        },
        "exact": {
          "coverage": 0.994,
          "mean_width_pp": 19.524506610461774
        }
      },
      {
        "budget": 260,
        "method": "power-score",
        "rmse_pp": 1.2802192694170882,
        "bias_pp": 0.03333867120589955,
        "mae_pp": 1.0109693678265739,
        "normal": {
          "coverage": 0.945,
          "mean_width_pp": 4.946176092609316,
          "median_width_pp": 4.947868748044199
        },
        "exact": {
          "coverage": 0.994,
          "mean_width_pp": 19.524506610461774
        }
      },
      {
        "budget": 521,
        "method": "uniform",
        "rmse_pp": 0.7959886318495861,
        "bias_pp": -0.037501819394007964,
        "mae_pp": 0.6470273840121564,
        "normal": {
          "coverage": 0.959,
          "mean_width_pp": 3.205312404989909,
          "median_width_pp": 3.208108037268781
        },
        "exact": {
          "coverage": 0.955,
          "mean_width_pp": 7.413623299482659
        }
      },
      {
        "budget": 521,
        "method": "K4",
        "rmse_pp": 0.5923105706657774,
        "bias_pp": 0.019421556510360836,
        "mae_pp": 0.4732755996685085,
        "normal": {
          "coverage": 0.951,
          "mean_width_pp": 2.368659585280792,
          "median_width_pp": 2.370952132513715
        },
        "exact": {
          "coverage": 0.994,
          "mean_width_pp": 16.035926422686337
        }
      },
      {
        "budget": 521,
        "method": "power-score",
        "rmse_pp": 0.7519271584342306,
        "bias_pp": 0.01458575742149195,
        "mae_pp": 0.5948538428704605,
        "normal": {
          "coverage": 0.959,
          "mean_width_pp": 3.089771389031514,
          "median_width_pp": 3.091589435656028
        },
        "exact": {
          "coverage": 0.994,
          "mean_width_pp": 16.035926422686337
        }
      },
      {
        "budget": 1043,
        "method": "uniform",
        "rmse_pp": 0.5544819062572988,
        "bias_pp": -0.005537102569133379,
        "mae_pp": 0.4413428294153755,
        "normal": {
          "coverage": 0.941,
          "mean_width_pp": 2.136379418007542,
          "median_width_pp": 2.1390978483615655
        },
        "exact": {
          "coverage": 0.961,
          "mean_width_pp": 4.915156160183943
        }
      },
      {
        "budget": 1043,
        "method": "K4",
        "rmse_pp": 0.3628769032779995,
        "bias_pp": 0.008315989737471517,
        "mae_pp": 0.29209753897090557,
        "normal": {
          "coverage": 0.962,
          "mean_width_pp": 1.454106047862935,
          "median_width_pp": 1.454930264092802
        },
        "exact": {
          "coverage": 0.993,
          "mean_width_pp": 11.29087947882736
        }
      },
      {
        "budget": 1043,
        "method": "power-score",
        "rmse_pp": 0.48580544376799883,
        "bias_pp": 0.008956549964282412,
        "mae_pp": 0.38795314304883877,
        "normal": {
          "coverage": 0.95,
          "mean_width_pp": 1.8950554078012767,
          "median_width_pp": 1.894998926265412
        },
        "exact": {
          "coverage": 0.993,
          "mean_width_pp": 11.29087947882736
        }
      },
      {
        "budget": 2087,
        "method": "uniform",
        "rmse_pp": 0.33925151929285896,
        "bias_pp": 0.009552560648214076,
        "mae_pp": 0.2711445754795343,
        "normal": {
          "coverage": 0.946,
          "mean_width_pp": 1.3057266239463763,
          "median_width_pp": 1.3080046212875285
        },
        "exact": {
          "coverage": 0.953,
          "mean_width_pp": 2.990362138340678
        }
      },
      {
        "budget": 2087,
        "method": "K4",
        "rmse_pp": 0.17628666687547334,
        "bias_pp": 0.006309989951459777,
        "mae_pp": 0.13951618110436886,
        "normal": {
          "coverage": 0.948,
          "mean_width_pp": 0.696931092760288,
          "median_width_pp": 0.6969116403734932
        },
        "exact": {
          "coverage": 0.99,
          "mean_width_pp": 6.425215558536118
        }
      },
      {
        "budget": 2087,
        "method": "power-score",
        "rmse_pp": 0.22909639495324574,
        "bias_pp": 0.0142602514105508,
        "mae_pp": 0.17973844180833343,
        "normal": {
          "coverage": 0.945,
          "mean_width_pp": 0.9071323470121474,
          "median_width_pp": 0.9071575441293278
        },
        "exact": {
          "coverage": 0.99,
          "mean_width_pp": 6.425215558536118
        }
      }
    ],
    "comparisons": {
      "power-score/K4-b260": {
        "rmse_ratio": 1.351397066514586,
        "draw_bootstrap_95pct": [
          1.3071979102673683,
          1.3986512691494595
        ],
        "seed": 500000,
        "same_queries": true
      },
      "K4/uniform-b260": {
        "rmse_ratio": 0.814304279001564,
        "draw_bootstrap_95pct": [
          0.7631056662606881,
          0.8680282627915783
        ],
        "seed": 500000,
        "same_queries": false
      },
      "power-score/uniform-b260": {
        "rmse_ratio": 1.1004484138929884,
        "draw_bootstrap_95pct": [
          1.0332901806517307,
          1.172226731678388
        ],
        "seed": 500000,
        "same_queries": false
      },
      "power-score/K4-b521": {
        "rmse_ratio": 1.2694812412161387,
        "draw_bootstrap_95pct": [
          1.2202125849220373,
          1.3193408396274222
        ],
        "seed": 500001,
        "same_queries": true
      },
      "K4/uniform-b521": {
        "rmse_ratio": 0.7441193843302317,
        "draw_bootstrap_95pct": [
          0.7009754479106396,
          0.7922567670627765
        ],
        "seed": 500001,
        "same_queries": false
      },
      "power-score/uniform-b521": {
        "rmse_ratio": 0.9446455996325316,
        "draw_bootstrap_95pct": [
          0.889824229227783,
          1.004932153747736
        ],
        "seed": 500001,
        "same_queries": false
      },
      "power-score/K4-b1043": {
        "rmse_ratio": 1.3387609940989382,
        "draw_bootstrap_95pct": [
          1.2921608501833897,
          1.3831843428371837
        ],
        "seed": 500002,
        "same_queries": true
      },
      "K4/uniform-b1043": {
        "rmse_ratio": 0.6544431823346316,
        "draw_bootstrap_95pct": [
          0.6145664497481825,
          0.6967765314283239
        ],
        "seed": 500002,
        "same_queries": false
      },
      "power-score/uniform-b1043": {
        "rmse_ratio": 0.876143005363584,
        "draw_bootstrap_95pct": [
          0.8214914466656994,
          0.9328647894470578
        ],
        "seed": 500002,
        "same_queries": false
      },
      "power-score/K4-b2087": {
        "rmse_ratio": 1.2995673411595927,
        "draw_bootstrap_95pct": [
          1.247689292548761,
          1.3521054578184792
        ],
        "seed": 500003,
        "same_queries": true
      },
      "K4/uniform-b2087": {
        "rmse_ratio": 0.5196341264526331,
        "draw_bootstrap_95pct": [
          0.4884867477973134,
          0.5536800902106936
        ],
        "seed": 500003,
        "same_queries": false
      },
      "power-score/uniform-b2087": {
        "rmse_ratio": 0.675299540089836,
        "draw_bootstrap_95pct": [
          0.634822470883097,
          0.7203130177827298
        ],
        "seed": 500003,
        "same_queries": false
      }
    },
    "reference_prevalence": 0.27380724276681356
  },
  "childplay": {
    "primary_half_full_MC": {
      "rmse_ratio": 0.8946773418634837,
      "draw_bootstrap_95pct": [
        0.8712365068351794,
        0.919003322591215
      ],
      "seed": 400004,
      "resamples": 2000,
      "scope": "Monte Carlo uncertainty on fixed corpus; streams differ across controls"
    },
    "primary_budget": 1032,
    "reference_prevalence": 0.03518805738658395,
    "main_temporal_rmse_pp": 0.2765283147467882,
    "main_static_rmse_pp": 0.26030623539246656,
    "block_temporal_static_ratio": 1.1138552889660565
  },
  "variance": [
    {
      "dataset": "ChildPlay",
      "budget": 516,
      "A": 1.2414982037081342e-05,
      "B": 5.1741099321633395e-06,
      "C": 1.0424969307364124e-05,
      "half_minus_full_variance": -2.6446170483597536e-06,
      "exact_RMSE_ratio_half_over_full": 0.8878573051210343,
      "MC_RMSE_ratio_half_over_full": 0.9032193203253793
    },
    {
      "dataset": "ChildPlay",
      "budget": 1032,
      "A": 4.634948086362377e-06,
      "B": 1.9095479775749024e-06,
      "C": 3.849100685253157e-06,
      "half_minus_full_variance": -9.77277536364965e-07,
      "exact_RMSE_ratio_half_over_full": 0.889104295232226,
      "MC_RMSE_ratio_half_over_full": 0.8946773418634837
    },
    {
      "dataset": "ChildPlay",
      "budget": 2063,
      "A": 8.689568723227474e-07,
      "B": 3.290745553870571e-07,
      "C": 6.65537258813222e-07,
      "half_minus_full_variance": -1.7007838872285943e-07,
      "exact_RMSE_ratio_half_over_full": 0.8977321578017031,
      "MC_RMSE_ratio_half_over_full": 0.8910397971786643
    },
    {
      "dataset": "ChildPlay",
      "budget": 4126,
      "A": 1.4807663185395184e-08,
      "B": 1.9018311848372577e-10,
      "C": 8.391563639571209e-10,
      "half_minus_full_variance": -4.391841544841161e-10,
      "exact_RMSE_ratio_half_over_full": 0.9855110739749553,
      "MC_RMSE_ratio_half_over_full": 0.9853201298476075
    },
    {
      "dataset": "UCO",
      "budget": 260,
      "A": 0.00033154082546272824,
      "B": 0.00022565699817855015,
      "C": 0.0002133333470146166,
      "half_minus_full_variance": 6.56569879175877e-05,
      "exact_RMSE_ratio_half_over_full": 1.3045160497354682,
      "MC_RMSE_ratio_half_over_full": 1.3513970665145858
    },
    {
      "dataset": "UCO",
      "budget": 521,
      "A": 0.0001293408793210486,
      "B": 8.80334255325159e-05,
      "C": 8.327569885573417e-05,
      "half_minus_full_variance": 2.5576651390715266e-05,
      "exact_RMSE_ratio_half_over_full": 1.3037548882074612,
      "MC_RMSE_ratio_half_over_full": 1.269481241216139
    },
    {
      "dataset": "UCO",
      "budget": 1043,
      "A": 4.864837805295171e-05,
      "B": 3.311159928000623e-05,
      "C": 3.133069297927797e-05,
      "half_minus_full_variance": 9.613579545547753e-06,
      "exact_RMSE_ratio_half_over_full": 1.3034074349491653,
      "MC_RMSE_ratio_half_over_full": 1.3387609940989382
    },
    {
      "dataset": "UCO",
      "budget": 2087,
      "A": 1.1141440581115564e-05,
      "B": 7.5832110070011845e-06,
      "C": 7.185101663657456e-06,
      "half_minus_full_variance": 2.1943847592580926e-06,
      "exact_RMSE_ratio_half_over_full": 1.3016908759105321,
      "MC_RMSE_ratio_half_over_full": 1.2995673411595927
    }
  ],
  "checks": {
    "validated_draws": 12000,
    "bootstrap_comparisons": 12,
    "exact_variance_checks": 16,
    "stratum_dot_product_checks": 96,
    "sampled_frames_visually_reviewed": 75
  },
  "provenance": {
    "demo/research/data.json": {
      "sha256": "fbfbeb2855ff21f6a92296bd4dbc4547f93ecc29fb2b29d7609d4df6e30329b0",
      "manifest": "docs/research/h-evidence-manifest.json"
    },
    "docs/research/l-transfer-result.json": {
      "sha256": "35d37f00bd2c60c7b8e98812c6363002e150bb95e0875896864091aed74306f0",
      "manifest": "docs/research/l-transfer-evidence-manifest.json"
    },
    "docs/research/m-variance-result.json": {
      "sha256": "040d4e114942a9d42282da09c984e3476d8c929d22a13ceb60125fe4359357eb",
      "manifest": "docs/research/m-evidence-manifest.json"
    }
  }
};
