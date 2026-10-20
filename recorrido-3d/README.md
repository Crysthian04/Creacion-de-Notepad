# Recorrido integrado 3D: Edificio 2 (Postgrado, UTP)

Fuente editable del modelo que se hizo en Claude Design. Versión v3: corrige la física de la fuga de refrigerante en la Parada 3.

- Instrucciones y reglas para Claude Code: `CLAUDE.md`
- Plan de mejoras filtrado: `docs/PLAN_MEJORAS.md`
- Instrucción para pegar en Claude Code: `docs/PROMPT_CLAUDE_CODE.md` (fases 1–2) y `docs/PROMPT_FASE3.md` (después de la defensa)

```bash
npm install
npm run dev     # ver en http://localhost:5173
npm run build   # genera dist/Recorrido_integrado_Edificio2_offline.html
npm test        # prueba numérica de la calculadora psicrométrica
npm run check   # npm test + build + prueba de humo con capturas
```

three.js r184 (MIT) va en `vendor/`, sin cambios.
