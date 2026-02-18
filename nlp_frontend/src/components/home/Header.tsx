import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface HeaderProps {
    connected: boolean;
    username: string;
    dbUsername: string;
    onLogout: () => void;
}

const Header = ({ connected, username, dbUsername, onLogout }: HeaderProps) => {
    return (
        <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
            <div>
                <h2 className="font-semibold text-slate-800">Chat Interface</h2>
                <p className="text-sm text-slate-500">
                    Ask questions in natural language to query your database
                </p>
            </div>
            <div className="flex items-center gap-4">
                {connected && (
                    <div className="text-xs text-slate-400 mr-2">
                        DB: <span className="font-medium text-slate-600">{dbUsername}</span>
                    </div>
                )}
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onLogout}
                    className="text-xs text-slate-500 hover:text-red-500 h-8"
                >
                    Logout ({username})
                </Button>
                <Badge variant="outline" className="gap-1">
                    <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
                    {connected ? 'Connected' : 'Disconnected'}
                </Badge>
            </div>
        </div>
    );
};

export default Header;
