import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { LogOut } from "lucide-react";

interface HeaderProps {
    username: string;
    email?: string;
    onLogout: () => void;
}

const Header = ({ username, email, onLogout }: HeaderProps) => {
    const firstLetter = username?.charAt(0)?.toUpperCase() || "?";

    return (
        <div className="bg-white border-b px-6 py-4 relative">
            {/* Left side title */}
            <div>
                <h2 className="font-semibold text-slate-800">Chat Interface</h2>
                <p className="text-sm text-slate-500">
                    Ask questions in natural language to query your database
                </p>
            </div>

            {/* Right side avatar (top-right corner) */}
            <div className="absolute top-4 right-6">
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <button className="focus:outline-none transition-transform active:scale-95">
                            <Avatar className="h-9 w-9 border-2 border-slate-100 hover:border-purple-200 transition-colors">
                                <AvatarFallback className="bg-gradient-to-br from-purple-500 to-blue-500 text-white font-medium">
                                    {firstLetter}
                                </AvatarFallback>
                            </Avatar>
                        </button>
                    </DropdownMenuTrigger>

                    <DropdownMenuContent align="end" className="w-56">
                        <DropdownMenuLabel className="flex flex-col gap-1">
                            <span className="text-xs text-slate-500 font-normal">
                                Signed in as
                            </span>
                            <span className="truncate font-medium text-slate-800">
                                {username}
                            </span>
                            <span className="truncate text-sm text-slate-500">
                                {email}
                            </span>
                        </DropdownMenuLabel>

                        <DropdownMenuSeparator />

                        <DropdownMenuItem
                            className="gap-2 cursor-pointer text-red-600 focus:text-red-600 focus:bg-red-50"
                            onClick={onLogout}
                        >
                            <LogOut className="w-4 h-4" />
                            Logout
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>
        </div>
    );
};

export default Header;