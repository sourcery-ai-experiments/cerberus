export const fetchTags = async (url: string, search: string, tags: string[], limit: number = 5): Promise<string[]> => {
    const params = new URLSearchParams({
        startswith: search,
        limit: `${limit}`,
        tags: tags.join(","),
      });
    const response = await fetch(`${url}?${params.toString()}`);
    const data = await response.json();

    return data;
}
