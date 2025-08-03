export default defineNuxtRouteMiddleware(async (to, from) => {
  const authentication = useAuthentication()
  
  // Allow access to login and register pages
  if (to.path === '/login' || to.path === '/register') {
    return
  }
  
  // Wait for authentication check to complete if not already done
  if (!authentication.checkedLogin.value) {
    await authentication.checkAuthentication()
  }
  
  // Check if user is authenticated
  if (!authentication.isLoggedIn.value) {
    // Redirect to login page
    return navigateTo('/login')
  }
})
