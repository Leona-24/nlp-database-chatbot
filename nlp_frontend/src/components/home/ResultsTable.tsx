import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Download, CheckCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import { useState } from 'react';

import { toast } from 'sonner';
import type { QueryResult } from '../../types';

interface ResultsTableProps {
    result: QueryResult;
}

const ResultsTable = ({ result }: ResultsTableProps) => {
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 10;
    const totalPages = Math.ceil(result.rows.length / itemsPerPage);

    const exportCSV = () => {
        const csv = [
            result.columns.join(','),
            ...result.rows.map(row => row.join(','))
        ].join('\n');

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'query_results.csv';
        a.click();
        toast.success('Results exported to CSV');
    };

    const handlePageChange = (newPage: number) => {
        if (newPage >= 1 && newPage <= totalPages) {
            setCurrentPage(newPage);
        }
    };

    const currentRows = result.rows.slice(
        (currentPage - 1) * itemsPerPage,
        currentPage * itemsPerPage
    );

    return (
        <div className="mt-3">
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-xs">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        {result.rowCount} rows
                    </Badge>
                    <span className="text-xs text-slate-500">
                        {result.executionTime}s
                    </span>
                </div>
                <Button variant="outline" size="sm" className="h-7 text-xs" onClick={exportCSV}>
                    <Download className="w-3 h-3 mr-1" />
                    Export
                </Button>
            </div>

            <div className="border rounded-lg overflow-hidden bg-white shadow-sm">
                <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                        <thead className="bg-slate-50 border-b">
                            <tr>
                                {result.columns.map((col, idx) => (
                                    <th key={idx} className="px-4 py-3 text-left font-medium text-slate-700 whitespace-nowrap">
                                        {col}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {currentRows.map((row, rowIdx) => (
                                <tr key={rowIdx} className="hover:bg-slate-50 border-b last:border-0 transition-colors">
                                    {row.map((cell: any, cellIdx: number) => (
                                        <td key={cellIdx} className="px-4 py-3 text-slate-600 whitespace-nowrap">
                                            {String(cell)}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {totalPages > 1 && (
                    <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border-t">
                        <div className="text-xs text-slate-500">
                            Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, result.rows.length)} of {result.rows.length} entries
                        </div>
                        <div className="flex gap-1">
                            <Button
                                variant="outline"
                                size="sm"
                                className="h-7 w-7 p-0"
                                onClick={() => handlePageChange(currentPage - 1)}
                                disabled={currentPage === 1}
                            >
                                <ChevronLeft className="w-4 h-4" />
                            </Button>
                            <div className="flex items-center justify-center min-w-[2rem] text-xs font-medium">
                                {currentPage} / {totalPages}
                            </div>
                            <Button
                                variant="outline"
                                size="sm"
                                className="h-7 w-7 p-0"
                                onClick={() => handlePageChange(currentPage + 1)}
                                disabled={currentPage === totalPages}
                            >
                                <ChevronRight className="w-4 h-4" />
                            </Button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ResultsTable;
