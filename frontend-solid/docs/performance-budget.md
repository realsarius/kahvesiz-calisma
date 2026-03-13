# Performance Budget (Faz 1 Baseline)

## Targets

- Initial route JS payload target: `< 200KB gzip`
- Route-based code splitting: `enabled`
- Lazy loading: route components loaded with `lazy()` + `Suspense`
- Budget gate command: `npm run size:check`

## Measurement Flow

```bash
npm run build
npm run size:check
```

## Notes

- Budget checks the largest JS asset in `dist/assets` as initial payload candidate.
- Real production cutover oncesi bu metrik CI pipeline'ina tasinacak.
