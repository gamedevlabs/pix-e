import type { ChartOptions, ScriptableLineSegmentContext, ChartDataset, Color } from 'chart.js'

const skippedDash = (ctx: ScriptableLineSegmentContext, value: number[]) =>
  ctx.p0.skip || ctx.p1.skip ? value : undefined
const skippedColor = (ctx: ScriptableLineSegmentContext, value: Color) =>
  ctx.p0.skip || ctx.p1.skip ? value : undefined

function getDefaultLineDatasetOptions(color: string): Partial<ChartDataset<'line'>> {
  return {
    borderColor: color,
    pointBackgroundColor: color,
    segment: {
      borderDash: (ctx: ScriptableLineSegmentContext) => skippedDash(ctx, [6, 6]),
      borderColor: (ctx: ScriptableLineSegmentContext) => skippedColor(ctx, 'rgb(0,0,0,0.3)'),
    },
  }
}

const lineCategoryOptions: ChartOptions<'line'> = {
  responsive: true,
  maintainAspectRatio: true,
  spanGaps: true,
  elements: {
    line: {
      fill: true,
    },
    point: {
      radius: 4,
    },
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

const lineLinearOptions: ChartOptions<'line'> = {
  responsive: true,
  maintainAspectRatio: true,
  spanGaps: true,
  elements: {
    line: {
      fill: true,
    },
    point: {
      radius: 4,
    },
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

export { lineCategoryOptions, lineLinearOptions, getDefaultLineDatasetOptions }
