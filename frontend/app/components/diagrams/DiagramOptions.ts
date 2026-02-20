const skipped = (ctx, value) => (ctx.p0.skip || ctx.p1.skip ? value : undefined)

const lineCategoryOptions = {
  responsive: true,
  maintainAspectRatio: true,
  spanGaps: true,
  segment: {
    borderDash: (ctx) => skipped(ctx, [6, 6]),
    borderColor: (ctx) => skipped(ctx, 'rgb(0,0,0,0.3)'),
  },
  scales: {
    x: {
      ticks: {
        color: 'rgb(128, 128, 128)',
      },
      grid: {
        color: 'rgba(128, 128, 128, 0.2)',
      },
      border: {
        color: 'rgb(128, 128, 128)',
      },
      type: 'category',
    },
    y: {
      ticks: {
        color: 'rgb(128, 128, 128)',
      },
      grid: {
        color: 'rgba(128, 128, 128, 0.2)',
      },
      border: {
        color: 'rgb(128, 128, 128)',
      },
    },
  },
}

const lineLinearOptions = {
  responsive: true,
  maintainAspectRatio: true,
  spanGaps: true,
  segment: {
    borderDash: (ctx) => skipped(ctx, [6, 6]),
    borderColor: (ctx) => skipped(ctx, 'rgb(0,0,0,0.3)'),
  },
  scales: {
    x: {
      ticks: {
        color: 'rgb(128, 128, 128)',
      },
      grid: {
        color: 'rgba(128, 128, 128, 0.2)',
      },
      border: {
        color: 'rgb(128, 128, 128)',
      },
      type: 'linear',
    },
    y: {
      ticks: {
        color: 'rgb(128, 128, 128)',
      },
      grid: {
        color: 'rgba(128, 128, 128, 0.2)',
      },
      border: {
        color: 'rgb(128, 128, 128)',
      },
    },
  },
}

export { lineCategoryOptions, lineLinearOptions }
