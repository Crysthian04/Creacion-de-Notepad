// Matriz de confusion, metricas por clase con intervalos de Wilson.
// Generado por src/exportador_web.py el 2026-09-09.
// NO editar a mano: se regenera con `python -m src.exportador_web`.
// Cargar con <script src="..."></script>. No usa fetch ni módulos ES6.
const FDD_METRICAS = {
 "version_formato": 1,
 "clases": [
  "sano",
  "condensador_sucio",
  "incrustacion_evaporador",
  "caudal_agua_bajo",
  "carga_baja",
  "sobrecarga",
  "txv_restringida",
  "txv_sobrealimenta",
  "compresor_desgastado",
  "incondensables",
  "restriccion_linea_liquido"
 ],
 "nivel_discrepancia": 0.05,
 "modo_discrepancia": "por_condicion",
 "corrida_valida": true,
 "prueba_balanceada": {
  "conjunto": "prueba_balanceada",
  "n_muestras": 1997,
  "matriz_confusion": [
   [
    117,
    0,
    9,
    2,
    1,
    15,
    30,
    0,
    4,
    0,
    5
   ],
   [
    11,
    166,
    2,
    0,
    0,
    0,
    3,
    0,
    1,
    0,
    0
   ],
   [
    31,
    1,
    134,
    5,
    1,
    4,
    2,
    4,
    1,
    0,
    0
   ],
   [
    17,
    0,
    5,
    149,
    0,
    2,
    4,
    5,
    1,
    0,
    0
   ],
   [
    6,
    2,
    1,
    0,
    154,
    0,
    4,
    0,
    0,
    0,
    0
   ],
   [
    36,
    1,
    5,
    0,
    0,
    114,
    10,
    1,
    2,
    8,
    6
   ],
   [
    65,
    0,
    2,
    1,
    1,
    4,
    102,
    0,
    2,
    1,
    5
   ],
   [
    10,
    0,
    18,
    0,
    1,
    0,
    0,
    153,
    1,
    0,
    0
   ],
   [
    21,
    1,
    5,
    1,
    0,
    4,
    14,
    0,
    136,
    1,
    0
   ],
   [
    5,
    3,
    0,
    0,
    0,
    12,
    0,
    0,
    0,
    163,
    0
   ],
   [
    38,
    2,
    2,
    2,
    0,
    11,
    43,
    0,
    0,
    0,
    85
   ]
  ],
  "matriz_confusion_normalizada": [
   [
    0.639344262295082,
    0.0,
    0.04918032786885246,
    0.01092896174863388,
    0.00546448087431694,
    0.08196721311475409,
    0.16393442622950818,
    0.0,
    0.02185792349726776,
    0.0,
    0.0273224043715847
   ],
   [
    0.060109289617486336,
    0.907103825136612,
    0.01092896174863388,
    0.0,
    0.0,
    0.0,
    0.01639344262295082,
    0.0,
    0.00546448087431694,
    0.0,
    0.0
   ],
   [
    0.16939890710382513,
    0.00546448087431694,
    0.73224043715847,
    0.0273224043715847,
    0.00546448087431694,
    0.02185792349726776,
    0.01092896174863388,
    0.02185792349726776,
    0.00546448087431694,
    0.0,
    0.0
   ],
   [
    0.09289617486338798,
    0.0,
    0.0273224043715847,
    0.8142076502732241,
    0.0,
    0.01092896174863388,
    0.02185792349726776,
    0.0273224043715847,
    0.00546448087431694,
    0.0,
    0.0
   ],
   [
    0.03592814371257485,
    0.011976047904191617,
    0.005988023952095809,
    0.0,
    0.9221556886227545,
    0.0,
    0.023952095808383235,
    0.0,
    0.0,
    0.0,
    0.0
   ],
   [
    0.19672131147540983,
    0.00546448087431694,
    0.0273224043715847,
    0.0,
    0.0,
    0.6229508196721312,
    0.0546448087431694,
    0.00546448087431694,
    0.01092896174863388,
    0.04371584699453552,
    0.03278688524590164
   ],
   [
    0.3551912568306011,
    0.0,
    0.01092896174863388,
    0.00546448087431694,
    0.00546448087431694,
    0.02185792349726776,
    0.5573770491803278,
    0.0,
    0.01092896174863388,
    0.00546448087431694,
    0.0273224043715847
   ],
   [
    0.0546448087431694,
    0.0,
    0.09836065573770492,
    0.0,
    0.00546448087431694,
    0.0,
    0.0,
    0.8360655737704918,
    0.00546448087431694,
    0.0,
    0.0
   ],
   [
    0.11475409836065574,
    0.00546448087431694,
    0.0273224043715847,
    0.00546448087431694,
    0.0,
    0.02185792349726776,
    0.07650273224043716,
    0.0,
    0.7431693989071039,
    0.00546448087431694,
    0.0
   ],
   [
    0.0273224043715847,
    0.01639344262295082,
    0.0,
    0.0,
    0.0,
    0.06557377049180328,
    0.0,
    0.0,
    0.0,
    0.8907103825136612,
    0.0
   ],
   [
    0.20765027322404372,
    0.01092896174863388,
    0.01092896174863388,
    0.01092896174863388,
    0.0,
    0.060109289617486336,
    0.23497267759562843,
    0.0,
    0.0,
    0.0,
    0.4644808743169399
   ]
  ],
  "recall_por_clase": {
   "sano": 0.639344262295082,
   "condensador_sucio": 0.907103825136612,
   "incrustacion_evaporador": 0.73224043715847,
   "caudal_agua_bajo": 0.8142076502732241,
   "carga_baja": 0.9221556886227545,
   "sobrecarga": 0.6229508196721312,
   "txv_restringida": 0.5573770491803278,
   "txv_sobrealimenta": 0.8360655737704918,
   "compresor_desgastado": 0.7431693989071039,
   "incondensables": 0.8907103825136612,
   "restriccion_linea_liquido": 0.4644808743169399
  },
  "precision_por_clase": {
   "sano": 0.3277310924369748,
   "condensador_sucio": 0.9431818181818182,
   "incrustacion_evaporador": 0.73224043715847,
   "caudal_agua_bajo": 0.93125,
   "carga_baja": 0.9746835443037974,
   "sobrecarga": 0.6867469879518072,
   "txv_restringida": 0.4811320754716981,
   "txv_sobrealimenta": 0.9386503067484663,
   "compresor_desgastado": 0.918918918918919,
   "incondensables": 0.9421965317919075,
   "restriccion_linea_liquido": 0.8415841584158416
  },
  "f1_por_clase": {
   "sano": 0.43333333333333335,
   "condensador_sucio": 0.924791086350975,
   "incrustacion_evaporador": 0.73224043715847,
   "caudal_agua_bajo": 0.8688046647230321,
   "carga_baja": 0.9476923076923077,
   "sobrecarga": 0.6532951289398281,
   "txv_restringida": 0.5164556962025316,
   "txv_sobrealimenta": 0.884393063583815,
   "compresor_desgastado": 0.8217522658610272,
   "incondensables": 0.9157303370786517,
   "restriccion_linea_liquido": 0.5985915492957746
  },
  "soporte_por_clase": {
   "sano": 183,
   "condensador_sucio": 183,
   "incrustacion_evaporador": 183,
   "caudal_agua_bajo": 183,
   "carga_baja": 167,
   "sobrecarga": 183,
   "txv_restringida": 183,
   "txv_sobrealimenta": 183,
   "compresor_desgastado": 183,
   "incondensables": 183,
   "restriccion_linea_liquido": 183
  },
  "intervalos_wilson": {
   "sano": {
    "soporte": 183,
    "predichos": 357,
    "recall_ic95": [
     0.5675650408887386,
     0.705393443731389
    ],
    "precision_ic95": [
     0.28109887179871434,
     0.3780313393521065
    ],
    "soporte_pequeno": false
   },
   "condensador_sucio": {
    "soporte": 183,
    "predichos": 176,
    "recall_ic95": [
     0.8562759268623155,
     0.9411910184004098
    ],
    "precision_ic95": [
     0.8985816137448528,
     0.9688483913262764
    ],
    "soporte_pequeno": false
   },
   "incrustacion_evaporador": {
    "soporte": 183,
    "predichos": 183,
    "recall_ic95": [
     0.6637941541811011,
     0.7911366535191114
    ],
    "precision_ic95": [
     0.6637941541811011,
     0.7911366535191114
    ],
    "soporte_pequeno": false
   },
   "caudal_agua_bajo": {
    "soporte": 183,
    "predichos": 160,
    "recall_ic95": [
     0.7516043604890528,
     0.8638902616935875
    ],
    "precision_ic95": [
     0.8810959503315197,
     0.9611809805578271
    ],
    "soporte_pequeno": false
   },
   "carga_baja": {
    "soporte": 167,
    "predichos": 158,
    "recall_ic95": [
     0.8713799915330105,
     0.953945924403155
    ],
    "precision_ic95": [
     0.9367201325318171,
     0.9901120292856636
    ],
    "soporte_pequeno": false
   },
   "sobrecarga": {
    "soporte": 183,
    "predichos": 166,
    "recall_ic95": [
     0.5508832399093089,
     0.6899624818143331
    ],
    "precision_ic95": [
     0.6126394825128705,
     0.7524065368369237
    ],
    "soporte_pequeno": false
   },
   "txv_restringida": {
    "soporte": 183,
    "predichos": 212,
    "recall_ic95": [
     0.4849661191232457,
     0.6274285510144537
    ],
    "precision_ic95": [
     0.41480953896657424,
     0.5481262435702492
    ],
    "soporte_pequeno": false
   },
   "txv_sobrealimenta": {
    "soporte": 183,
    "predichos": 163,
    "recall_ic95": [
     0.7756226790586419,
     0.8826889603193125
    ],
    "precision_ic95": [
     0.8907619319125651,
     0.9663384555207849
    ],
    "soporte_pequeno": false
   },
   "compresor_desgastado": {
    "soporte": 183,
    "predichos": 148,
    "recall_ic95": [
     0.675325435128111,
     0.8010138811697585
    ],
    "precision_ic95": [
     0.8636284040808161,
     0.9530120949655586
    ],
    "soporte_pequeno": false
   },
   "incondensables": {
    "soporte": 183,
    "predichos": 173,
    "recall_ic95": [
     0.8372235285581803,
     0.9281306538080595
    ],
    "precision_ic95": [
     0.8968780598913775,
     0.9683029834830323
    ],
    "soporte_pequeno": false
   },
   "restriccion_linea_liquido": {
    "soporte": 183,
    "predichos": 101,
    "recall_ic95": [
     0.39369350674818765,
     0.536728840309427
    ],
    "precision_ic95": [
     0.7580624179833655,
     0.9000732838754386
    ],
    "soporte_pequeno": false
   }
  },
  "pr_auc_por_clase": {
   "sano": 0.3575580484302663,
   "condensador_sucio": 0.9683710034638513,
   "incrustacion_evaporador": 0.8309952895840792,
   "caudal_agua_bajo": 0.9360409105821937,
   "carga_baja": 0.9904796815748377,
   "sobrecarga": 0.7381149257957729,
   "txv_restringida": 0.5652951298910288,
   "txv_sobrealimenta": 0.957650722494362,
   "compresor_desgastado": 0.8879073995949602,
   "incondensables": 0.9591771698440587,
   "restriccion_linea_liquido": 0.6901343818569586
  },
  "f1_macro": 0.7542799882017952,
  "f1_ponderado": 0.7527303652113854,
  "pr_auc_macro": 0.8074295148283973,
  "exactitud_global": 0.7376064096144216,
  "proporcion_de_clases": {
   "sano": 0.09163745618427642,
   "condensador_sucio": 0.09163745618427642,
   "incrustacion_evaporador": 0.09163745618427642,
   "caudal_agua_bajo": 0.09163745618427642,
   "sobrecarga": 0.09163745618427642,
   "txv_restringida": 0.09163745618427642,
   "txv_sobrealimenta": 0.09163745618427642,
   "compresor_desgastado": 0.09163745618427642,
   "incondensables": 0.09163745618427642,
   "restriccion_linea_liquido": 0.09163745618427642,
   "carga_baja": 0.08362543815723586
  }
 },
 "prevalencia_realista": {
  "conjunto": "prevalencia_realista",
  "n_muestras": 9964,
  "matriz_confusion": [
   [
    4313,
    93,
    408,
    58,
    30,
    275,
    1139,
    83,
    240,
    16,
    88
   ],
   [
    32,
    690,
    7,
    0,
    4,
    2,
    11,
    0,
    6,
    10,
    0
   ],
   [
    116,
    2,
    434,
    2,
    7,
    19,
    20,
    16,
    5,
    0,
    2
   ],
   [
    58,
    1,
    21,
    427,
    0,
    3,
    11,
    0,
    10,
    0,
    1
   ],
   [
    18,
    4,
    0,
    0,
    327,
    0,
    13,
    0,
    1,
    0,
    0
   ],
   [
    14,
    1,
    0,
    1,
    0,
    52,
    3,
    0,
    2,
    3,
    1
   ],
   [
    91,
    1,
    6,
    1,
    1,
    12,
    172,
    0,
    20,
    1,
    9
   ],
   [
    2,
    0,
    6,
    0,
    0,
    0,
    0,
    20,
    0,
    0,
    0
   ],
   [
    30,
    2,
    5,
    1,
    0,
    5,
    15,
    2,
    188,
    0,
    1
   ],
   [
    1,
    0,
    0,
    0,
    0,
    9,
    1,
    0,
    1,
    110,
    0
   ],
   [
    28,
    0,
    2,
    0,
    0,
    9,
    36,
    0,
    7,
    0,
    69
   ]
  ],
  "matriz_confusion_normalizada": [
   [
    0.6396262791042563,
    0.01379208067625686,
    0.06050719264422364,
    0.008601512679816105,
    0.0044490582826635025,
    0.040783034257748776,
    0.16891591279845766,
    0.012309061248702359,
    0.03559246626130802,
    0.0023728310840872013,
    0.013050570962479609
   ],
   [
    0.04199475065616798,
    0.905511811023622,
    0.009186351706036745,
    0.0,
    0.005249343832020997,
    0.0026246719160104987,
    0.014435695538057743,
    0.0,
    0.007874015748031496,
    0.013123359580052493,
    0.0
   ],
   [
    0.18619582664526485,
    0.0032102728731942215,
    0.6966292134831461,
    0.0032102728731942215,
    0.011235955056179775,
    0.030497592295345103,
    0.03210272873194221,
    0.025682182985553772,
    0.008025682182985553,
    0.0,
    0.0032102728731942215
   ],
   [
    0.10902255639097744,
    0.0018796992481203006,
    0.039473684210526314,
    0.8026315789473685,
    0.0,
    0.005639097744360902,
    0.020676691729323307,
    0.0,
    0.018796992481203006,
    0.0,
    0.0018796992481203006
   ],
   [
    0.049586776859504134,
    0.011019283746556474,
    0.0,
    0.0,
    0.9008264462809917,
    0.0,
    0.03581267217630854,
    0.0,
    0.0027548209366391185,
    0.0,
    0.0
   ],
   [
    0.18181818181818182,
    0.012987012987012988,
    0.0,
    0.012987012987012988,
    0.0,
    0.6753246753246753,
    0.03896103896103896,
    0.0,
    0.025974025974025976,
    0.03896103896103896,
    0.012987012987012988
   ],
   [
    0.2898089171974522,
    0.0031847133757961785,
    0.01910828025477707,
    0.0031847133757961785,
    0.0031847133757961785,
    0.03821656050955414,
    0.5477707006369427,
    0.0,
    0.06369426751592357,
    0.0031847133757961785,
    0.028662420382165606
   ],
   [
    0.07142857142857142,
    0.0,
    0.21428571428571427,
    0.0,
    0.0,
    0.0,
    0.0,
    0.7142857142857143,
    0.0,
    0.0,
    0.0
   ],
   [
    0.12048192771084337,
    0.008032128514056224,
    0.020080321285140562,
    0.004016064257028112,
    0.0,
    0.020080321285140562,
    0.060240963855421686,
    0.008032128514056224,
    0.7550200803212851,
    0.0,
    0.004016064257028112
   ],
   [
    0.00819672131147541,
    0.0,
    0.0,
    0.0,
    0.0,
    0.07377049180327869,
    0.00819672131147541,
    0.0,
    0.00819672131147541,
    0.9016393442622951,
    0.0
   ],
   [
    0.18543046357615894,
    0.0,
    0.013245033112582781,
    0.0,
    0.0,
    0.059602649006622516,
    0.23841059602649006,
    0.0,
    0.046357615894039736,
    0.0,
    0.45695364238410596
   ]
  ],
  "recall_por_clase": {
   "sano": 0.6396262791042563,
   "condensador_sucio": 0.905511811023622,
   "incrustacion_evaporador": 0.6966292134831461,
   "caudal_agua_bajo": 0.8026315789473685,
   "carga_baja": 0.9008264462809917,
   "sobrecarga": 0.6753246753246753,
   "txv_restringida": 0.5477707006369427,
   "txv_sobrealimenta": 0.7142857142857143,
   "compresor_desgastado": 0.7550200803212851,
   "incondensables": 0.9016393442622951,
   "restriccion_linea_liquido": 0.45695364238410596
  },
  "precision_por_clase": {
   "sano": 0.9170742079523708,
   "condensador_sucio": 0.8690176322418136,
   "incrustacion_evaporador": 0.4881889763779528,
   "caudal_agua_bajo": 0.8714285714285714,
   "carga_baja": 0.8861788617886179,
   "sobrecarga": 0.13471502590673576,
   "txv_restringida": 0.12104152005629838,
   "txv_sobrealimenta": 0.1652892561983471,
   "compresor_desgastado": 0.39166666666666666,
   "incondensables": 0.7857142857142857,
   "restriccion_linea_liquido": 0.40350877192982454
  },
  "f1_por_clase": {
   "sano": 0.7536257207758169,
   "condensador_sucio": 0.8868894601542416,
   "incrustacion_evaporador": 0.5740740740740741,
   "caudal_agua_bajo": 0.8356164383561644,
   "carga_baja": 0.8934426229508197,
   "sobrecarga": 0.22462203023758098,
   "txv_restringida": 0.19827089337175793,
   "txv_sobrealimenta": 0.2684563758389262,
   "compresor_desgastado": 0.5157750342935528,
   "incondensables": 0.8396946564885496,
   "restriccion_linea_liquido": 0.42857142857142855
  },
  "soporte_por_clase": {
   "sano": 6743,
   "condensador_sucio": 762,
   "incrustacion_evaporador": 623,
   "caudal_agua_bajo": 532,
   "carga_baja": 363,
   "sobrecarga": 77,
   "txv_restringida": 314,
   "txv_sobrealimenta": 28,
   "compresor_desgastado": 249,
   "incondensables": 122,
   "restriccion_linea_liquido": 151
  },
  "intervalos_wilson": {
   "sano": {
    "soporte": 6743,
    "predichos": 4703,
    "recall_ic95": [
     0.6280901709711575,
     0.6510033829667325
    ],
    "precision_ic95": [
     0.9088480468498976,
     0.9246195591133028
    ],
    "soporte_pequeno": false
   },
   "condensador_sucio": {
    "soporte": 762,
    "predichos": 794,
    "recall_ic95": [
     0.8826612800226559,
     0.9242941008289456
    ],
    "precision_ic95": [
     0.8437625670048795,
     0.8907190644367501
    ],
    "soporte_pequeno": false
   },
   "incrustacion_evaporador": {
    "soporte": 623,
    "predichos": 889,
    "recall_ic95": [
     0.6594154072545229,
     0.7314329346551398
    ],
    "precision_ic95": [
     0.4554515491445069,
     0.5210280414122054
    ],
    "soporte_pequeno": false
   },
   "caudal_agua_bajo": {
    "soporte": 532,
    "predichos": 490,
    "recall_ic95": [
     0.7666917768870817,
     0.8342320782223388
    ],
    "precision_ic95": [
     0.8388758585536364,
     0.8982025892725491
    ],
    "soporte_pequeno": false
   },
   "carga_baja": {
    "soporte": 363,
    "predichos": 369,
    "recall_ic95": [
     0.8657553951431526,
     0.9275025123569783
    ],
    "precision_ic95": [
     0.849717361015219,
     0.914682319707104
    ],
    "soporte_pequeno": false
   },
   "sobrecarga": {
    "soporte": 77,
    "predichos": 386,
    "recall_ic95": [
     0.5645787430085915,
     0.7694077194067986
    ],
    "precision_ic95": [
     0.10423183519939822,
     0.17239744192238665
    ],
    "soporte_pequeno": false
   },
   "txv_restringida": {
    "soporte": 314,
    "predichos": 1421,
    "recall_ic95": [
     0.492472369185024,
     0.6019142686874256
    ],
    "precision_ic95": [
     0.10509594279541296,
     0.139030562213986
    ],
    "soporte_pequeno": false
   },
   "txv_sobrealimenta": {
    "soporte": 28,
    "predichos": 121,
    "recall_ic95": [
     0.529403642629825,
     0.8474618415167003
    ],
    "precision_ic95": [
     0.10962203759241997,
     0.24155577493161046
    ],
    "soporte_pequeno": true
   },
   "compresor_desgastado": {
    "soporte": 249,
    "predichos": 480,
    "recall_ic95": [
     0.6979917098385267,
     0.804299052441098
    ],
    "precision_ic95": [
     0.34902388240750626,
     0.43602973844692217
    ],
    "soporte_pequeno": false
   },
   "incondensables": {
    "soporte": 122,
    "predichos": 140,
    "recall_ic95": [
     0.8359212414818843,
     0.9428355448272535
    ],
    "precision_ic95": [
     0.7105941206983544,
     0.8455732189307932
    ],
    "soporte_pequeno": false
   },
   "restriccion_linea_liquido": {
    "soporte": 151,
    "predichos": 171,
    "recall_ic95": [
     0.3795510128200621,
     0.5364922210395724
    ],
    "precision_ic95": [
     0.3328765728547405,
     0.4783811598587556
    ],
    "soporte_pequeno": false
   }
  },
  "pr_auc_por_clase": {
   "sano": 0.9231533310498021,
   "condensador_sucio": 0.9540967344464082,
   "incrustacion_evaporador": 0.7100608062494955,
   "caudal_agua_bajo": 0.8863083323575796,
   "carga_baja": 0.9576823429909664,
   "sobrecarga": 0.3734298266722448,
   "txv_restringida": 0.20564013473792161,
   "txv_sobrealimenta": 0.7011040774180703,
   "compresor_desgastado": 0.7565481164052952,
   "incondensables": 0.9387111467751497,
   "restriccion_linea_liquido": 0.5191645457669817
  },
  "f1_macro": 0.5835489759193556,
  "f1_ponderado": 0.7292933081121175,
  "pr_auc_macro": 0.7205363086245378,
  "exactitud_global": 0.6826575672420715,
  "proporcion_de_clases": {
   "sano": 0.6767362505018065,
   "condensador_sucio": 0.07647531112003211,
   "incrustacion_evaporador": 0.06252509032517062,
   "caudal_agua_bajo": 0.053392211963067045,
   "carga_baja": 0.036431152147731835,
   "txv_restringida": 0.03151344841429145,
   "compresor_desgastado": 0.024989963869931756,
   "restriccion_linea_liquido": 0.015154556403050983,
   "incondensables": 0.012244078683259736,
   "sobrecarga": 0.007727820152549177,
   "txv_sobrealimenta": 0.0028101164191087916
  }
 },
 "sensibilidad_al_ruido": {
  "0.5": {
   "f1_macro": 0.8172096923199418,
   "exactitud": 0.8118279569892473,
   "diagnostico_incipiente": 0.6235294117647059,
   "deteccion_incipiente": 0.788235294117647,
   "n_filas": 3921
  },
  "1.0": {
   "f1_macro": 0.7571982354968086,
   "exactitud": 0.7455197132616488,
   "diagnostico_incipiente": 0.4823529411764706,
   "deteccion_incipiente": 0.788235294117647,
   "n_filas": 3921
  },
  "2.0": {
   "f1_macro": 0.6460273609250021,
   "exactitud": 0.6308243727598566,
   "diagnostico_incipiente": 0.36470588235294116,
   "deteccion_incipiente": 0.8058823529411765,
   "n_filas": 3921
  }
 },
 "sensibilidad_a_la_discrepancia": {
  "0.0": {
   "f1_macro": 0.8198440920105189,
   "exactitud": 0.8154121863799283,
   "diagnostico_incipiente": 0.6411764705882353,
   "deteccion_incipiente": 0.8294117647058824,
   "n_filas": 3921
  },
  "0.03": {
   "f1_macro": 0.7699564516268894,
   "exactitud": 0.7616487455197133,
   "diagnostico_incipiente": 0.5294117647058824,
   "deteccion_incipiente": 0.7764705882352941,
   "n_filas": 3921
  },
  "0.05": {
   "f1_macro": 0.7571982354968086,
   "exactitud": 0.7455197132616488,
   "diagnostico_incipiente": 0.4823529411764706,
   "deteccion_incipiente": 0.788235294117647,
   "n_filas": 3921
  },
  "0.08": {
   "f1_macro": 0.7490616609146535,
   "exactitud": 0.7383512544802867,
   "diagnostico_incipiente": 0.5117647058823529,
   "deteccion_incipiente": 0.788235294117647,
   "n_filas": 3921
  },
  "0.15": {
   "f1_macro": 0.6638020119895689,
   "exactitud": 0.6523297491039427,
   "diagnostico_incipiente": 0.3941176470588235,
   "deteccion_incipiente": 0.7705882352941177,
   "n_filas": 3921
  }
 },
 "repeticiones_por_corrida": {
  "nivel_discrepancia": 0.05,
  "n_repeticiones": 5,
  "modo": "por_corrida",
  "corridas": [
   {
    "f1_macro": 0.8023572745457247,
    "exactitud": 0.7938517179023508,
    "diagnostico_incipiente": 0.5941176470588235,
    "deteccion_incipiente": 0.7470588235294118,
    "n_filas": 3919,
    "semilla": 20261902
   },
   {
    "f1_macro": 0.7866555992659248,
    "exactitud": 0.7827648114901257,
    "diagnostico_incipiente": 0.5764705882352941,
    "deteccion_incipiente": 0.7941176470588235,
    "n_filas": 3920,
    "semilla": 20262902
   },
   {
    "f1_macro": 0.8006542062854041,
    "exactitud": 0.7924865831842576,
    "diagnostico_incipiente": 0.6058823529411764,
    "deteccion_incipiente": 0.8294117647058824,
    "n_filas": 3922,
    "semilla": 20263902
   },
   {
    "f1_macro": 0.7985349539093601,
    "exactitud": 0.7920433996383364,
    "diagnostico_incipiente": 0.6,
    "deteccion_incipiente": 0.7588235294117647,
    "n_filas": 3922,
    "semilla": 20264902
   },
   {
    "f1_macro": 0.7869023737059403,
    "exactitud": 0.7765765765765765,
    "diagnostico_incipiente": 0.5529411764705883,
    "deteccion_incipiente": 0.7941176470588235,
    "n_filas": 3920,
    "semilla": 20265902
   }
  ],
  "f1_macro_media": 0.7950208815424709,
  "f1_macro_desv": 0.0076451591156655235,
  "f1_macro_min": 0.7866555992659248,
  "f1_macro_max": 0.8023572745457247,
  "diagnostico_incipiente_media": 0.5858823529411765,
  "diagnostico_incipiente_desv": 0.02145245003389465
 },
 "contraste_con_la_fisica": {
  "condensador_sucio": {
   "residuo_caracteristico_esperado": "res_split_cond",
   "residuo_dominante_en_los_datos": "res_split_cond",
   "puesto_del_esperado_en_los_datos": 1,
   "residuo_raiz_del_arbol": "res_split_cond",
   "coincide_en_los_datos": true,
   "coincide_en_el_arbol": true,
   "entre_los_tres_primeros": true,
   "esta_entre_los_declarados": true,
   "exactitud_del_arbol": 0.980225988700565
  },
  "incrustacion_evaporador": {
   "residuo_caracteristico_esperado": "res_approach_ev",
   "residuo_dominante_en_los_datos": "res_approach_ev",
   "puesto_del_esperado_en_los_datos": 1,
   "residuo_raiz_del_arbol": "res_approach_ev",
   "coincide_en_los_datos": true,
   "coincide_en_el_arbol": true,
   "entre_los_tres_primeros": true,
   "esta_entre_los_declarados": true,
   "exactitud_del_arbol": 0.8559322033898306
  },
  "caudal_agua_bajo": {
   "residuo_caracteristico_esperado": "res_dT_agua_ev",
   "residuo_dominante_en_los_datos": "res_dT_agua_ev",
   "puesto_del_esperado_en_los_datos": 1,
   "residuo_raiz_del_arbol": "res_dT_agua_ev",
   "coincide_en_los_datos": true,
   "coincide_en_el_arbol": true,
   "entre_los_tres_primeros": true,
   "esta_entre_los_declarados": true,
   "exactitud_del_arbol": 0.9463276836158192
  },
  "carga_baja": {
   "residuo_caracteristico_esperado": "res_SC",
   "residuo_dominante_en_los_datos": "res_SC",
   "puesto_del_esperado_en_los_datos": 1,
   "residuo_raiz_del_arbol": "res_SC",
   "coincide_en_los_datos": true,
   "coincide_en_el_arbol": true,
   "entre_los_tres_primeros": true,
   "esta_entre_los_declarados": true,
   "exactitud_del_arbol": 0.9821428571428571
  },
  "sobrecarga": {
   "residuo_caracteristico_esperado": "res_SC",
   "residuo_dominante_en_los_datos": "res_SC",
   "puesto_del_esperado_en_los_datos": 1,
   "residuo_raiz_del_arbol": "res_SC",
   "coincide_en_los_datos": true,
   "coincide_en_el_arbol": true,
   "entre_los_tres_primeros": true,
   "esta_entre_los_declarados": true,
   "exactitud_del_arbol": 0.9067796610169492
  },
  "txv_restringida": {
   "residuo_caracteristico_esperado": "res_SH_evap",
   "residuo_dominante_en_los_datos": "res_SH_total",
   "puesto_del_esperado_en_los_datos": 2,
   "residuo_raiz_del_arbol": "res_SH_total",
   "coincide_en_los_datos": false,
   "coincide_en_el_arbol": false,
   "entre_los_tres_primeros": true,
   "esta_entre_los_declarados": true,
   "exactitud_del_arbol": 0.7288135593220338
  },
  "txv_sobrealimenta": {
   "residuo_caracteristico_esperado": "res_SH_evap",
   "residuo_dominante_en_los_datos": "res_SH_total",
   "puesto_del_esperado_en_los_datos": 2,
   "residuo_raiz_del_arbol": "res_SH_total",
   "coincide_en_los_datos": false,
   "coincide_en_el_arbol": false,
   "entre_los_tres_primeros": true,
   "esta_entre_los_declarados": true,
   "exactitud_del_arbol": 0.9463276836158192
  },
  "compresor_desgastado": {
   "residuo_caracteristico_esperado": "res_SH_des",
   "residuo_dominante_en_los_datos": "res_SH_des",
   "puesto_del_esperado_en_los_datos": 1,
   "residuo_raiz_del_arbol": "res_SH_des",
   "coincide_en_los_datos": true,
   "coincide_en_el_arbol": true,
   "entre_los_tres_primeros": true,
   "esta_entre_los_declarados": true,
   "exactitud_del_arbol": 0.9067796610169492
  },
  "incondensables": {
   "residuo_caracteristico_esperado": "res_split_cond",
   "residuo_dominante_en_los_datos": "res_split_cond",
   "puesto_del_esperado_en_los_datos": 1,
   "residuo_raiz_del_arbol": "res_SC",
   "coincide_en_los_datos": true,
   "coincide_en_el_arbol": false,
   "entre_los_tres_primeros": true,
   "esta_entre_los_declarados": true,
   "exactitud_del_arbol": 0.9887005649717514
  },
  "restriccion_linea_liquido": {
   "residuo_caracteristico_esperado": "res_SH_evap",
   "residuo_dominante_en_los_datos": "res_SC",
   "puesto_del_esperado_en_los_datos": 3,
   "residuo_raiz_del_arbol": "res_SC",
   "coincide_en_los_datos": false,
   "coincide_en_el_arbol": false,
   "entre_los_tres_primeros": true,
   "esta_entre_los_declarados": false,
   "exactitud_del_arbol": 0.8248587570621468
  }
 },
 "deteccion_vs_severidad": {
  "carga_baja": {
   "(0.15, 0.25]": 0.75,
   "(0.25, 0.35]": 0.8181818181818182,
   "(0.35, 0.45]": 1.0,
   "(0.45, 0.55]": 1.0,
   "(0.55, 0.65]": 1.0,
   "(0.65, 0.75]": 1.0,
   "(0.75, 0.85]": 1.0,
   "(0.85, 0.95]": 1.0
  },
  "caudal_agua_bajo": {
   "(0.15, 0.25]": 0.4375,
   "(0.25, 0.35]": 0.6206896551724138,
   "(0.35, 0.45]": 0.9090909090909091,
   "(0.45, 0.55]": 0.9,
   "(0.55, 0.65]": 0.9473684210526315,
   "(0.65, 0.75]": 1.0,
   "(0.75, 0.85]": 1.0,
   "(0.85, 0.95]": 1.0
  },
  "compresor_desgastado": {
   "(0.15, 0.25]": 0.2413793103448276,
   "(0.25, 0.35]": 0.46875,
   "(0.35, 0.45]": 0.7619047619047619,
   "(0.45, 0.55]": 0.9166666666666666,
   "(0.55, 0.65]": 0.9375,
   "(0.65, 0.75]": 1.0,
   "(0.75, 0.85]": 1.0,
   "(0.85, 0.95]": 1.0
  },
  "condensador_sucio": {
   "(0.15, 0.25]": 0.5483870967741935,
   "(0.25, 0.35]": 0.9,
   "(0.35, 0.45]": 1.0,
   "(0.45, 0.55]": 1.0,
   "(0.55, 0.65]": 1.0,
   "(0.65, 0.75]": 1.0,
   "(0.75, 0.85]": 1.0,
   "(0.85, 0.95]": 1.0
  },
  "incondensables": {
   "(0.15, 0.25]": 0.45161290322580644,
   "(0.25, 0.35]": 0.9,
   "(0.35, 0.45]": 1.0,
   "(0.45, 0.55]": 1.0,
   "(0.55, 0.65]": 1.0,
   "(0.65, 0.75]": 1.0,
   "(0.75, 0.85]": 1.0,
   "(0.85, 0.95]": 1.0
  },
  "incrustacion_evaporador": {
   "(0.15, 0.25]": 0.4375,
   "(0.25, 0.35]": 0.5517241379310345,
   "(0.35, 0.45]": 0.45,
   "(0.45, 0.55]": 0.8333333333333334,
   "(0.55, 0.65]": 0.9565217391304348,
   "(0.65, 0.75]": 0.8421052631578947,
   "(0.75, 0.85]": 1.0,
   "(0.85, 0.95]": 1.0
  },
  "restriccion_linea_liquido": {
   "(0.15, 0.25]": 0.03125,
   "(0.25, 0.35]": 0.034482758620689655,
   "(0.35, 0.45]": 0.0,
   "(0.45, 0.55]": 0.3157894736842105,
   "(0.55, 0.65]": 0.8888888888888888,
   "(0.65, 0.75]": 1.0,
   "(0.75, 0.85]": 1.0,
   "(0.85, 0.95]": 1.0
  },
  "sobrecarga": {
   "(0.15, 0.25]": 0.11764705882352941,
   "(0.25, 0.35]": 0.4074074074074074,
   "(0.35, 0.45]": 0.47058823529411764,
   "(0.45, 0.55]": 0.9166666666666666,
   "(0.55, 0.65]": 0.8,
   "(0.65, 0.75]": 0.85,
   "(0.75, 0.85]": 0.85,
   "(0.85, 0.95]": 0.9047619047619048
  },
  "txv_restringida": {
   "(0.15, 0.25]": 0.30303030303030304,
   "(0.25, 0.35]": 0.42857142857142855,
   "(0.35, 0.45]": 0.55,
   "(0.45, 0.55]": 0.3888888888888889,
   "(0.55, 0.65]": 0.6521739130434783,
   "(0.65, 0.75]": 0.7222222222222222,
   "(0.75, 0.85]": 0.7083333333333334,
   "(0.85, 0.95]": 0.8947368421052632
  },
  "txv_sobrealimenta": {
   "(0.15, 0.25]": 0.34615384615384615,
   "(0.25, 0.35]": 0.7428571428571429,
   "(0.35, 0.45]": 0.8421052631578947,
   "(0.45, 0.55]": 0.9411764705882353,
   "(0.55, 0.65]": 1.0,
   "(0.65, 0.75]": 1.0,
   "(0.75, 0.85]": 1.0,
   "(0.85, 0.95]": 1.0
  }
 },
 "desacuerdo_100_vs_300": {
  "n_validacion": 1929,
  "desacuerdo": 55,
  "fraccion_desacuerdo": 0.02851218247796786,
  "tabla_2x2": {
   "100_acierta_300_acierta": 0,
   "100_acierta_300_falla": 16,
   "100_falla_300_acierta": 16,
   "100_falla_300_falla": 23
  },
  "exactitud_100": 0.7506480041472265,
  "exactitud_300": 0.7506480041472265,
  "f1_macro_100": 0.7607835018322455,
  "f1_macro_300": 0.7611116259481652
 }
};
