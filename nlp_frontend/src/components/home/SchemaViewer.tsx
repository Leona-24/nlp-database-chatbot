import { Table } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface SchemaViewerProps {
    schema: any[];
}

const SchemaViewer = ({ schema }: SchemaViewerProps) => {
    if (!schema || schema.length === 0) return (
        <div className="text-center p-8 text-slate-400 text-sm">
            No schema available. Connect to a database to view tables.
        </div>
    );

    return (
        <Card className="border-0 shadow-none">
            <CardHeader className="p-4 pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                    <Table className="w-4 h-4" />
                    Database Schema
                    <Badge variant="secondary" className="ml-auto text-xs font-normal">
                        {schema.length} Tables
                    </Badge>
                </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-2">
                <div className="space-y-4">
                    {schema.map((table) => (
                        <div key={table.name} className="border rounded-lg p-3 bg-white">
                            <h4 className="font-medium text-sm text-slate-800 mb-2 flex items-center justify-between">
                                {table.name}
                            </h4>
                            <div className="space-y-1">
                                {table.columns.map((col: any) => (
                                    <div key={col.name} className="flex items-center justify-between text-xs group">
                                        <span className="flex items-center gap-2 text-slate-600 group-hover:text-slate-900">
                                            {col.primary_key && <span className="w-1.5 h-1.5 bg-yellow-400 rounded-full" title="Primary Key" />}
                                            {col.foreign_key && <span className="w-1.5 h-1.5 bg-blue-400 rounded-full" title="Foreign Key" />}
                                            {!col.primary_key && !col.foreign_key && <span className="w-1.5 h-1.5 bg-slate-300 rounded-full" />}
                                            {col.name}
                                        </span>
                                        <span className="text-slate-400 font-mono text-[10px]">{col.type}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
};

export default SchemaViewer;
