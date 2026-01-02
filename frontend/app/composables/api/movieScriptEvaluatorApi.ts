export function useMovieScriptEvaluatorApi() {
  const config = useRuntimeConfig()

  async function uploadFile(projectId: string, file: File) {
    try {
      const formData = new FormData()
      formData.append('title', 'new movie script')
      formData.append('project', projectId)
      formData.append('file', file)

      return await $fetch(
        `${config.public.apiBase}/movie-script-evaluator/${projectId}/assets/upload-script/`,
        {
          method: 'POST',
          body: formData,
          credentials: 'include',
          headers: {
            'X-CSRFToken': useCookie('csrftoken').value,
          } as HeadersInit,
        },
      )
    } catch (error) {
      console.error('Error fetching: ', error)
    }
  }

  return {
    uploadFile,
  }
}
