import type { PageConfig } from '~/types/page-config'

export default defineNuxtRouteMiddleware(async (to) => {
  // Check if page has custom config
  const pageConfig = to.meta.pageConfig as PageConfig | undefined

  // Skip middleware if page is public or standalone
  if (pageConfig?.type === 'public' || pageConfig?.type === 'standalone') {
    return
  }

  const { isLoggedIn, checkedLogin, checkAuthentication } = useAuthentication()
  if (!checkedLogin.value) {
    await checkAuthentication()
  }
  if (!isLoggedIn.value) {
    return
  }

  const { currentProjectId, fetchProjectById } = useProjectHandler()

  // Extract project ID from query parameter
  const projectIdFromUrl = Number(to.query.id)

  // If no project ID in URL and no current project, redirect to projects list
  if (!Number.isFinite(projectIdFromUrl) && !currentProjectId.value) {
    // Redirect with error info in query params
    return navigateTo({
      path: '/',
      query: {
        error: 'no-project',
        message: 'Please select a project to use this module',
      },
    })
  }

  // If URL has a project ID, validate it exists
  // Only validate if it's different from the current project
  if (
    Number.isFinite(projectIdFromUrl) &&
    projectIdFromUrl !== currentProjectId.value
  ) {
    const project = await fetchProjectById(projectIdFromUrl)

    if (!project) {
      // Project doesn't exist - redirect with error info
      return navigateTo({
        path: '/',
        query: {
          error: 'project-not-found',
          projectId: projectIdFromUrl,
        },
      })
    }

    // Project exists, set it in context
    //await selectProject(project.id)
  }
})
