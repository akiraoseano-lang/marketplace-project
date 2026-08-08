import { fetchAPI } from "../utils/fetch";
import { environment } from "../constants/environment";

export const getProducts = async () => {
    let url = `${environment.API_URL}/api/products`;

    const result = await fetchAPI(url, {
        method: 'GET'
    })

    return result
}