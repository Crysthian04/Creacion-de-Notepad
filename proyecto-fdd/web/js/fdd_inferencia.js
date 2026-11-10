// Inferencia de referencia del clasificador FDD, en JavaScript plano.
//
// Sin fetch, sin XMLHttpRequest, sin módulos ES6: se carga con
//     <script src="js/fdd_inferencia.js"></script>
// después de fdd_modelo.js, fdd_fisica.js y fdd_malla.js.
//
// EQUIVALENCIA EXACTA CON scikit-learn
// ------------------------------------
// Tres detalles del código fuente de scikit-learn gobiernan esta implementación
// y no son opcionales:
//
// 1. `ForestClassifier._validate_X_predict` convierte X a float32 antes de
//    recorrer los árboles, así que la comparación `x <= umbral` se hace sobre un
//    float32 promovido a doble. Aquí se aplica `Math.fround` a cada
//    característica. Sin eso, un residuo que difiera en el octavo dígito puede
//    tomar la rama contraria.
// 2. `DecisionTreeClassifier.predict_proba` devuelve `tree_.value` TAL CUAL, sin
//    normalizar. Por eso las hojas se usan verbatim y NO se renormalizan: sus
//    sumas valen 1 solo salvo error de redondeo, y renormalizar cambiaría los
//    bits del resultado.
// 3. `ForestClassifier.predict_proba` acumula `out += prediccion` árbol por
//    árbol y divide al final: suma LINEAL, no por pares. Aquí se acumula en el
//    mismo orden de árboles y se divide una sola vez al final.
//
// La prueba `tests/test_exportador.py` verifica la igualdad exacta contra
// scikit-learn sobre las 1997 muestras del conjunto de prueba.

var FDD = (function () {
  "use strict";

  function indiceImpuras(arbol) {
    if (arbol._mapa) return arbol._mapa;
    var mapa = {};
    for (var k = 0; k < arbol.impuras.length; k++) mapa[arbol.impuras[k].h] = arbol.impuras[k].v;
    arbol._mapa = mapa;
    return mapa;
  }

  // Recorre un árbol y devuelve el nodo hoja alcanzado.
  function recorrer(arbol, x) {
    var nodo = 0;
    while (arbol.izq[nodo] !== -1) {
      nodo = (x[arbol.feature[nodo]] <= arbol.umbral[nodo]) ? arbol.izq[nodo] : arbol.der[nodo];
    }
    return nodo;
  }

  // Probabilidades por clase. Réplica exacta de RandomForestClassifier.predict_proba.
  function probabilidades(residuos) {
    var M = FDD_MODELO, nC = M.clases.length, nA = M.arboles.length;
    var x = new Array(M.columnas_entrada.length), i, k;
    for (i = 0; i < M.columnas_entrada.length; i++) {
      // FALLO RUIDOSO, NO SILENCIOSO.
      //
      // `Math.fround(null)` vale 0 y `Math.fround(undefined)` vale NaN. Los
      // nodos de la malla sin estado estacionario llevan TODOS sus residuos en
      // `null`, así que sin esta comprobación entraban al bosque como un vector
      // de ceros —es decir, como una máquina perfectamente sana— y el bosque
      // devolvía `sano` con aire de certeza. Un punto donde el modelo no tiene
      // solución física no se clasifica: se rechaza.
      var v = residuos[M.columnas_entrada[i]];
      if (typeof v !== "number" || !isFinite(v)) {
        throw new Error("residuo no finito en `" + M.columnas_entrada[i] + "`: "
                        + v + ". El bosque no clasifica un punto incompleto.");
      }
      // float32, como hace scikit-learn antes de recorrer los árboles
      x[i] = Math.fround(v);
    }
    var acum = new Array(nC);
    for (k = 0; k < nC; k++) acum[k] = 0.0;

    for (var a = 0; a < nA; a++) {
      var arbol = M.arboles[a];
      var nodo = recorrer(arbol, x);
      var h = arbol.hoja[nodo];
      if (arbol.tipo_hoja[h] === 1) {
        acum[arbol.clase_pura[h]] += 1.0;               // hoja pura: exactamente 1,0
      } else {
        var v = indiceImpuras(arbol)[h];
        for (k = 0; k < nC; k++) acum[k] += v[k];
      }
    }
    for (k = 0; k < nC; k++) acum[k] /= nA;
    return acum;
  }

  // Clase predicha. argmax con desempate por el índice menor, como numpy.
  function predecir(residuos) {
    var pr = probabilidades(residuos), mejor = 0;
    for (var k = 1; k < pr.length; k++) if (pr[k] > pr[mejor]) mejor = k;
    return {clase_id: mejor, clase: FDD_MODELO.clases[mejor], probabilidades: pr,
            confianza: pr[mejor]};
  }

  // ---------------------------------------------------------------------
  // Consulta de la malla
  // ---------------------------------------------------------------------
  function buscarCelda(eje, v) {
    if (v <= eje[0]) return {i: 0, t: 0.0};
    if (v >= eje[eje.length - 1]) return {i: eje.length - 2, t: 1.0};
    var i = 0;
    while (i < eje.length - 2 && eje[i + 1] < v) i++;
    return {i: i, t: (v - eje[i]) / (eje[i + 1] - eje[i])};
  }

  // Entrada canónica a la malla: la fracción de carga.
  function indicePorCarga(q) { return buscarCelda(FDD_MALLA.cargas, q); }

  // Conveniencia documentada. NO es válida bajo falla de caudal de agua: con
  // caudal degradado, la misma carga produce un retorno más alto y esta relación
  // devolvería el punto equivocado. La temperatura de retorno REAL está en el
  // campo `T_sec_in_ev` de la malla.
  function indicePorRetorno(tRetorno) {
    var q = (tRetorno - FDD_FISICA.setpoint_agua_C) / FDD_FISICA.dT_agua_nominal_K;
    return indicePorCarga(q);
  }

  // Fracción de carga a partir de una demanda en vatios.
  function cargaDesdeVatios(w) { return w / FDD_FISICA.Q_nom_W; }

  function indicePlano(iT, iQ, iClase, iSev) {
    return ((iT * FDD_MALLA.nCargas + iQ) * FDD_MALLA.nClases + iClase)
           * FDD_MALLA.nSeveridades + iSev;
  }

  function indiceSeveridad(f) {
    var sev = FDD_MALLA.severidades, mejor = 0, d = Infinity;
    for (var k = 0; k < sev.length; k++) {
      var dk = Math.abs(sev[k] - f);
      if (dk < d) { d = dk; mejor = k; }
    }
    return mejor;
  }

  // Estado del ciclo en (T_amb, carga, clase, severidad).
  //
  // Regla de interpolación: bilineal SOLO si las cuatro esquinas de la celda
  // comparten régimen; si no, vecino más próximo. Interpolar entre regímenes
  // distintos produce estados que la máquina no tiene. Los campos discretos son
  // siempre vecino más próximo.
  function consultar(tAmb, carga, clase, severidad) {
    var cT = buscarCelda(FDD_MALLA.temperaturas_C, tAmb);
    var cQ = indicePorCarga(carga);
    var iC = FDD_MALLA.clases.indexOf(clase);
    if (iC < 0) throw new Error("clase desconocida: " + clase);
    var iS = (clase === "sano") ? 0 : indiceSeveridad(severidad);

    var e = [indicePlano(cT.i, cQ.i, iC, iS), indicePlano(cT.i + 1, cQ.i, iC, iS),
             indicePlano(cT.i, cQ.i + 1, iC, iS), indicePlano(cT.i + 1, cQ.i + 1, iC, iS)];
    var reg = FDD_MALLA.discretos.regimen_cod;
    var conv = FDD_MALLA.discretos.convergio;
    var vecino = e[(cT.t < 0.5 ? 0 : 1) + (cQ.t < 0.5 ? 0 : 2)];

    // Regla de interpolación: la decide el exportador y viaja en `celda_bilineal`,
    // para que Python y JavaScript no puedan divergir. Vale 0 cuando la celda
    // toca ciclado, cambia el régimen de la válvula o alguna esquina no
    // converge; en esos casos se toma el vecino más próximo, porque interpolar
    // entre regímenes distintos devuelve estados que la máquina no tiene.
    var todosConv = conv[e[0]] && conv[e[1]] && conv[e[2]] && conv[e[3]];
    var idxCelda = ((cT.i * (FDD_MALLA.cargas.length - 1) + cQ.i) * FDD_MALLA.nClases + iC)
                   * FDD_MALLA.nSeveridades + iS;
    var uniforme = FDD_MALLA.celda_bilineal[idxCelda] === 1;

    var salida = {_interpolacion: (uniforme && todosConv) ? "bilineal" : "vecino",
                  _regimen: FDD_MALLA.regimenes[reg[vecino]],
                  _sin_estado_estacionario: !conv[vecino]};
    var campos = FDD_MALLA.datos, c;
    for (c in campos) {
      if (!Object.prototype.hasOwnProperty.call(campos, c)) continue;
      var v = campos[c];
      if (uniforme && todosConv) {
        salida[c] = (1 - cT.t) * (1 - cQ.t) * v[e[0]] + cT.t * (1 - cQ.t) * v[e[1]]
                  + (1 - cT.t) * cQ.t * v[e[2]] + cT.t * cQ.t * v[e[3]];
      } else {
        salida[c] = v[vecino];
      }
    }
    for (c in FDD_MALLA.discretos) {            // discretos: siempre vecino
      if (!Object.prototype.hasOwnProperty.call(FDD_MALLA.discretos, c)) continue;
      salida[c] = FDD_MALLA.discretos[c][vecino];
    }
    return salida;
  }

  // Diagnóstico completo: consulta la malla y clasifica sus residuos.
  //
  // RECHAZA los puntos sin estado estacionario en lugar de clasificarlos. La
  // malla trae 189 nodos con `convergio = 0`; clasificarlos devolvía `sano` con
  // confianza 0,348, que es el peor resultado posible: el punto donde el modelo
  // no sabe nada se presentaba como la máquina en buen estado. No están todos en
  // la zona de carga baja —18 de ellos están a carga plena—, así que la
  // comprobación no se puede sustituir por un aviso sobre una banda de carga.
  function diagnosticar(tAmb, carga, clase, severidad) {
    var estado = consultar(tAmb, carga, clase, severidad);
    if (!estado.convergio) {
      return {estado: estado, residuos: null, diagnostico: null,
              motivo: "sin estado estacionario: el modelo no tiene solución en este punto"};
    }
    var residuos = {};
    for (var k = 0; k < FDD_MODELO.columnas_entrada.length; k++) {
      var col = FDD_MODELO.columnas_entrada[k];
      residuos[col] = estado[col];
    }
    return {estado: estado, residuos: residuos, diagnostico: predecir(residuos),
            motivo: ""};
  }

  return {predecir: predecir, probabilidades: probabilidades, consultar: consultar,
          diagnosticar: diagnosticar, indicePorCarga: indicePorCarga,
          indicePorRetorno: indicePorRetorno, cargaDesdeVatios: cargaDesdeVatios,
          indicePlano: indicePlano, indiceSeveridad: indiceSeveridad};
})();

if (typeof module !== "undefined" && module.exports) { module.exports = FDD; }
