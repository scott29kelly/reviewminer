'use client';

import { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ReviewsTable } from '@/components/data-tables/reviews-table';
import { useReviews, useDeleteReview, useBulkDeleteReviews, useImportReviews } from '@/lib/hooks';
import { Review } from '@/lib/api';
import {
  Search,
  Upload,
  Trash2,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  X,
  FileUp,
  Star,
} from 'lucide-react';
import { toast } from 'sonner';
import { useDropzone } from 'react-dropzone';

export default function ReviewsPage() {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [search, setSearch] = useState('');
  const [source, setSource] = useState<string>('');
  const [processed, setProcessed] = useState<string>('');
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [selectedReview, setSelectedReview] = useState<Review | null>(null);
  const [showImport, setShowImport] = useState(false);

  const { data, isLoading, refetch } = useReviews({
    page,
    page_size: pageSize,
    search: search || undefined,
    source: source || undefined,
    processed: processed === '' ? undefined : processed === 'true',
  });

  const deleteReview = useDeleteReview();
  const bulkDelete = useBulkDeleteReviews();
  const importReviews = useImportReviews();

  const handleDelete = async (id: number) => {
    try {
      await deleteReview.mutateAsync(id);
      toast.success('Review deleted');
    } catch (e: any) {
      toast.error(e.message || 'Failed to delete');
    }
  };

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return;
    try {
      await bulkDelete.mutateAsync(selectedIds);
      toast.success(`Deleted ${selectedIds.length} reviews`);
      setSelectedIds([]);
    } catch (e: any) {
      toast.error(e.message || 'Failed to delete');
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    try {
      const result = await importReviews.mutateAsync({ file });
      toast.success(result.message);
      setShowImport(false);
      refetch();
    } catch (e: any) {
      toast.error(e.message || 'Import failed');
    }
  }, [importReviews, refetch]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/json': ['.json'],
    },
    maxFiles: 1,
  });

  const clearFilters = () => {
    setSearch('');
    setSource('');
    setProcessed('');
    setPage(1);
  };

  const hasFilters = search || source || processed;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight">Reviews</h1>
          <p className="text-muted-foreground">
            {data?.total ?? 0} reviews collected from various sources
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          {selectedIds.length > 0 && (
            <Button
              variant="destructive"
              onClick={handleBulkDelete}
              disabled={bulkDelete.isPending}
              className="shadow-lg shadow-destructive/25"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete {selectedIds.length}
            </Button>
          )}
          <Button 
            onClick={() => setShowImport(true)}
            className="bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white shadow-lg shadow-indigo-500/25"
          >
            <Upload className="mr-2 h-4 w-4" />
            Import
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="border-border/50 shadow-sm">
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[200px]">
              <Label htmlFor="search" className="sr-only">Search</Label>
              <div className="relative">
                <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="search"
                  placeholder="Search reviews..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                  }}
                  className="pl-10 h-11 rounded-xl border-border/50 bg-muted/50 focus:bg-background transition-colors"
                />
              </div>
            </div>

            <div className="w-[160px]">
              <Label htmlFor="source" className="sr-only">Source</Label>
              <Select value={source || 'all'} onValueChange={(v) => { setSource(v === 'all' ? '' : v); setPage(1); }}>
                <SelectTrigger id="source" className="h-11 rounded-xl border-border/50">
                  <SelectValue placeholder="All sources" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All sources</SelectItem>
                  <SelectItem value="reddit">Reddit</SelectItem>
                  <SelectItem value="google">Google</SelectItem>
                  <SelectItem value="yelp">Yelp</SelectItem>
                  <SelectItem value="bbb">BBB</SelectItem>
                  <SelectItem value="amazon">Amazon</SelectItem>
                  <SelectItem value="manual">Manual</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="w-[160px]">
              <Label htmlFor="status" className="sr-only">Status</Label>
              <Select value={processed || 'all'} onValueChange={(v) => { setProcessed(v === 'all' ? '' : v); setPage(1); }}>
                <SelectTrigger id="status" className="h-11 rounded-xl border-border/50">
                  <SelectValue placeholder="All status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All status</SelectItem>
                  <SelectItem value="true">Processed</SelectItem>
                  <SelectItem value="false">Pending</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {hasFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters} className="h-11 rounded-xl">
                <X className="mr-2 h-4 w-4" />
                Clear
              </Button>
            )}

            <Button 
              variant="outline" 
              size="icon" 
              onClick={() => refetch()} 
              className="h-11 w-11 rounded-xl border-border/50"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      {isLoading ? (
        <Card className="border-border/50 shadow-sm">
          <CardContent className="pt-6">
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-14 w-full rounded-xl" />
              ))}
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          <ReviewsTable
            data={data?.reviews ?? []}
            onDelete={handleDelete}
            onViewDetails={setSelectedReview}
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
          />

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Page {data.page} of {data.total_pages} ({data.total} total)
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="rounded-xl border-border/50"
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                  disabled={page === data.total_pages}
                  className="rounded-xl border-border/50"
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Review Detail Dialog */}
      <Dialog open={!!selectedReview} onOpenChange={() => setSelectedReview(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-auto rounded-2xl">
          <DialogHeader>
            <DialogTitle className="text-xl">{selectedReview?.product_title || 'Review Details'}</DialogTitle>
            <DialogDescription>
              <div className="flex flex-wrap items-center gap-2 mt-3">
                <Badge 
                  variant="outline" 
                  className="rounded-lg capitalize bg-muted/50"
                >
                  {selectedReview?.source}
                </Badge>
                {selectedReview?.rating && (
                  <div className="flex items-center gap-1 text-amber-500">
                    {[...Array(5)].map((_, i) => (
                      <Star
                        key={i}
                        className={`h-4 w-4 ${i < selectedReview.rating ? 'fill-current' : 'stroke-current fill-transparent opacity-30'}`}
                      />
                    ))}
                  </div>
                )}
                <Badge 
                  variant={selectedReview?.processed ? 'default' : 'secondary'}
                  className="rounded-lg"
                >
                  {selectedReview?.processed ? 'Processed' : 'Pending'}
                </Badge>
              </div>
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4 p-4 rounded-xl bg-muted/50 border border-border/50">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {selectedReview?.review_text}
            </p>
          </div>
          {selectedReview?.author && (
            <p className="text-sm text-muted-foreground mt-2">
              — {selectedReview.author}
              {selectedReview.review_date && `, ${selectedReview.review_date}`}
            </p>
          )}
        </DialogContent>
      </Dialog>

      {/* Import Dialog */}
      <Dialog open={showImport} onOpenChange={setShowImport}>
        <DialogContent className="rounded-2xl">
          <DialogHeader>
            <DialogTitle className="text-xl">Import Reviews</DialogTitle>
            <DialogDescription>
              Upload a CSV or JSON file containing reviews
            </DialogDescription>
          </DialogHeader>
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all
              ${isDragActive 
                ? 'border-indigo-500 bg-indigo-500/5 scale-[1.02]' 
                : 'border-border/50 hover:border-indigo-500/50 hover:bg-muted/50'}
            `}
          >
            <input {...getInputProps()} />
            <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500/20 to-violet-500/20 mb-4">
              <FileUp className="h-7 w-7 text-indigo-500" />
            </div>
            {isDragActive ? (
              <p className="font-medium text-indigo-500">Drop the file here...</p>
            ) : (
              <>
                <p className="font-medium">Drag & drop a file here</p>
                <p className="text-sm text-muted-foreground mt-1">
                  or click to select (CSV or JSON)
                </p>
              </>
            )}
          </div>
          <div className="text-xs text-muted-foreground p-4 rounded-xl bg-muted/50 border border-border/50">
            <p className="font-medium mb-2">Expected format:</p>
            <p className="font-mono">CSV: review_text, product_title, author, rating, review_date</p>
            <p className="font-mono">JSON: array of objects with the same fields</p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
