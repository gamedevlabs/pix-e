import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Tooltip,
  Legend,
  Title,
} from 'chart.js'

export default defineNuxtPlugin(() => {
  // Register the pieces you actually use
  ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    LineElement,
    PointElement,
    ArcElement,
    Tooltip,
    Legend,
    Title,
  )

  // (optional) set any global defaults here
  // ChartJS.defaults.responsive = true
  // ChartJS.defaults.maintainAspectRatio = false
})
