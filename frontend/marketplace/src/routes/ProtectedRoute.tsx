import { type ReactNode } from "react";
import { useNavigate, useLocation } from "react-router-dom";


interface PropTypes {
    children: ReactNode;
}

const ProtectedRoute = (props: PropTypes) => {
    const { children } = props;

    const auth = cookieStore.get('auth');
    
}

export default ProtectedRoute;