import type { RouteObject } from "react-router-dom";
import Home from "../components/pages";

const routes: RouteObject[] = [
    {
        path: '/',
        element: <Home />
    }
]

export default routes;