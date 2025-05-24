export default defineNuxtRouteMiddleware(async (to) => {
  const { isLoggedIn, checkedLogin, checkAuthentication } = useAuthentication()

  if (!checkedLogin.value) {
    await checkAuthentication()
  }
  if (!isLoggedIn.value) {
    return navigateTo(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
  }
})
