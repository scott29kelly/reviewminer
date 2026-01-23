'use client';

import { useState } from 'react';
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
  getSortedRowModel,
  SortingState,
  RowSelectionState,
} from '@tanstack/react-table';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Review } from '@/lib/api';
import { format } from 'date-fns';
import { MoreHorizontal, ArrowUpDown, ExternalLink, Trash2, MessageSquareText } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ReviewsTableProps {
  data: Review[];
  onDelete?: (id: number) => void;
  onViewDetails?: (review: Review) => void;
  selectedIds?: number[];
  onSelectionChange?: (ids: number[]) => void;
}

export function ReviewsTable({
  data,
  onDelete,
  onViewDetails,
  selectedIds = [],
  onSelectionChange,
}: ReviewsTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});

  const columns: ColumnDef<Review>[] = [
    {
      id: 'select',
      header: ({ table }) => (
        <Checkbox
          checked={table.getIsAllPageRowsSelected()}
          onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
          aria-label="Select all"
        />
      ),
      cell: ({ row }) => (
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={(value) => row.toggleSelected(!!value)}
          aria-label="Select row"
        />
      ),
      enableSorting: false,
    },
    {
      accessorKey: 'source',
      header: 'Source',
      cell: ({ row }) => (
        <Badge variant="outline" className="capitalize">
          {row.getValue('source')}
        </Badge>
      ),
    },
    {
      accessorKey: 'product_title',
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="-ml-4"
        >
          Product
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => {
        const title = row.getValue('product_title') as string;
        return (
          <div className="max-w-[200px] truncate" title={title}>
            {title || '—'}
          </div>
        );
      },
    },
    {
      accessorKey: 'rating',
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="-ml-4"
        >
          Rating
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => {
        const rating = row.getValue('rating') as number | null;
        if (!rating) return '—';
        return (
          <div className="flex items-center gap-1">
            {'★'.repeat(rating)}
            {'☆'.repeat(5 - rating)}
          </div>
        );
      },
    },
    {
      accessorKey: 'review_text',
      header: 'Review',
      cell: ({ row }) => {
        const text = row.getValue('review_text') as string;
        return (
          <div className="max-w-[300px] truncate text-muted-foreground" title={text}>
            {text}
          </div>
        );
      },
    },
    {
      accessorKey: 'processed',
      header: 'Status',
      cell: ({ row }) => {
        const processed = row.getValue('processed') as boolean;
        return (
          <Badge variant={processed ? 'default' : 'secondary'}>
            {processed ? 'Processed' : 'Pending'}
          </Badge>
        );
      },
    },
    {
      accessorKey: 'scraped_at',
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="-ml-4"
        >
          Date
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => {
        const date = row.getValue('scraped_at') as string;
        if (!date) return '—';
        return format(new Date(date), 'MMM d, yyyy');
      },
    },
    {
      id: 'actions',
      cell: ({ row }) => {
        const review = row.original;
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onViewDetails?.(review)}>
                View Details
              </DropdownMenuItem>
              {review.source_url && (
                <DropdownMenuItem asChild>
                  <a href={review.source_url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="mr-2 h-4 w-4" />
                    View Source
                  </a>
                </DropdownMenuItem>
              )}
              <DropdownMenuItem
                onClick={() => onDelete?.(review.id)}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: setSorting,
    onRowSelectionChange: (updater) => {
      const newSelection = typeof updater === 'function' ? updater(rowSelection) : updater;
      setRowSelection(newSelection);
      const selectedRows = Object.keys(newSelection)
        .filter((key) => newSelection[key])
        .map((key) => data[parseInt(key)]?.id)
        .filter(Boolean);
      onSelectionChange?.(selectedRows);
    },
    state: {
      sorting,
      rowSelection,
    },
  });

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <TableHead key={header.id}>
                  {header.isPlaceholder
                    ? null
                    : flexRender(header.column.columnDef.header, header.getContext())}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows?.length ? (
            table.getRowModel().rows.map((row) => (
              <TableRow key={row.id} data-state={row.getIsSelected() && 'selected'}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-32">
                <div className="flex flex-col items-center justify-center text-center">
                  <div className="rounded-full bg-muted p-3 mb-3">
                    <MessageSquareText className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <p className="text-sm font-medium text-muted-foreground">No reviews found</p>
                  <p className="text-xs text-muted-foreground/70 mt-1">
                    Try adjusting your filters or import some reviews
                  </p>
                </div>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
