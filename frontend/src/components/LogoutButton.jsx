import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthProvider.jsx";

export default function LogoutButton({ className = "" }) {
    const { logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate("/login");
    };

    return (
        <button
            className={`bg-sage-600 hover:bg-sage-700 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium ${className}`}
            onClick={handleLogout}
        >
            Logout
        </button>
    );
}