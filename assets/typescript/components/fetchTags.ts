export const fetchTags = async (url: string, search: string): Promise<string[]> => {
    const response = await fetch(`${url}?startswith=${search}`);
    const data = await response.json();

    return data;
}
