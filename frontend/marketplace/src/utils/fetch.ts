export const fetchAPI = async (url: string, option: RequestInit) => {
    const response = await fetch(url, {
        headers: {
            'Content-Type': 'Application/json'
        },
        ...option?.headers,
    });

    const data = await response.json();
    return data;
};