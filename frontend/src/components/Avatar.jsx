import { useAuth } from "../context/AuthProvider.jsx";
import generic from "../assets/generic_pfp.png";

export default function Avatar() {
    const { user } = useAuth();
    const username = user?.username || "Guest";

    return (
        <div className="flex items-center gap-2 max-w-[200px]">
            <img className="w-10 h-10 rounded-full flex-shrink-0" src={generic} alt="Avatar" />
            <div className="font-medium text-sage-800 truncate">
                {username}
            </div>
        </div>
    );
}