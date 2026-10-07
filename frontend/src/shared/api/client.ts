export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api/v1${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError(0, 'Nie udało się połączyć z serwerem. Spróbuj ponownie za chwilę.')
  }
  if (!response.ok) {
    const message =
      response.status === 404
        ? 'Nie znaleziono tych danych.'
        : response.status === 422
          ? 'Sprawdź wprowadzone dane i spróbuj ponownie.'
          : 'Dane są teraz niedostępne. Spróbuj ponownie za chwilę.'
    throw new ApiError(response.status, message)
  }
  return response.json() as Promise<T>
}
