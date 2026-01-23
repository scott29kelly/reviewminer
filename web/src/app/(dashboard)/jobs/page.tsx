'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import { Checkbox } from '@/components/ui/checkbox';
import { useJobs, useCreateJob, useCancelJob } from '@/lib/hooks';
import { Job, createJobWebSocket } from '@/lib/api';
import { Plus, Play, Square, RefreshCw, Clock, CheckCircle2, XCircle, Loader2, Rocket, Sparkles, ShoppingCart, BookOpen, MessageSquare, Library } from 'lucide-react';
import { EmptyState } from '@/components/empty-state';
import { toast } from 'sonner';
import { format, formatDistanceToNow } from 'date-fns';

const sourceOptions = [
  { value: 'amazon', label: 'Amazon', description: 'Search books by topic on Amazon', icon: ShoppingCart, color: 'text-orange-500' },
  { value: 'goodreads', label: 'Goodreads', description: 'Search books by topic on Goodreads', icon: BookOpen, color: 'text-amber-600' },
  { value: 'reddit', label: 'Reddit', description: 'Search Reddit for topic discussions', icon: MessageSquare, color: 'text-orange-600' },
  { value: 'librarything', label: 'LibraryThing', description: 'Search books by topic on LibraryThing', icon: Library, color: 'text-blue-500' },
];

const statusConfig = {
  pending: { 
    icon: Clock, 
    color: 'text-amber-500',
    bg: 'bg-amber-500/10 dark:bg-amber-500/20',
    badge: 'secondary'
  },
  running: { 
    icon: Loader2, 
    color: 'text-indigo-500',
    bg: 'bg-indigo-500/10 dark:bg-indigo-500/20',
    badge: 'default',
    animate: true
  },
  completed: { 
    icon: CheckCircle2, 
    color: 'text-emerald-500',
    bg: 'bg-emerald-500/10 dark:bg-emerald-500/20',
    badge: 'default'
  },
  failed: { 
    icon: XCircle, 
    color: 'text-rose-500',
    bg: 'bg-rose-500/10 dark:bg-rose-500/20',
    badge: 'destructive'
  },
};

function JobCard({ job, onCancel }: { job: Job; onCancel: (id: number) => void }) {
  const config = statusConfig[job.status];
  const StatusIcon = config.icon;
  const isRunning = job.status === 'running';

  return (
    <Card className="border-border/50 shadow-sm hover:shadow-md transition-shadow">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${config.bg}`}>
              <StatusIcon
                className={`h-5 w-5 ${config.color} ${config.animate ? 'animate-spin' : ''}`}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="capitalize rounded-lg bg-muted/50 border-border/50">
                  {job.source}
                </Badge>
                <Badge
                  variant={config.badge as any}
                  className="rounded-lg capitalize"
                >
                  {job.status}
                </Badge>
              </div>
              <p className="text-sm font-semibold">{job.query}</p>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                {job.started_at && (
                  <span>Started {formatDistanceToNow(new Date(job.started_at), { addSuffix: true })}</span>
                )}
                {job.reviews_found > 0 && (
                  <span className="font-medium text-foreground">{job.reviews_found} reviews found</span>
                )}
              </div>
              {job.error_message && (
                <p className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2 mt-2">
                  {job.error_message}
                </p>
              )}
            </div>
          </div>
          {isRunning && (
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => onCancel(job.id)}
              className="rounded-xl border-border/50 hover:bg-destructive/10 hover:text-destructive hover:border-destructive/50"
            >
              <Square className="mr-2 h-3 w-3" />
              Cancel
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function JobsPage() {
  const [showNewJob, setShowNewJob] = useState(false);
  const [selectedSources, setSelectedSources] = useState<Set<string>>(new Set(['amazon']));
  const [query, setQuery] = useState('');
  const [maxReviews, setMaxReviews] = useState('50');
  const [subreddits, setSubreddits] = useState('books,suggestmeabook');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data, isLoading, refetch } = useJobs();
  const createJob = useCreateJob();
  const cancelJob = useCancelJob();

  const toggleSource = (source: string) => {
    const newSet = new Set(selectedSources);
    if (newSet.has(source)) {
      newSet.delete(source);
    } else {
      newSet.add(source);
    }
    setSelectedSources(newSet);
  };

  const selectAllSources = () => {
    setSelectedSources(new Set(sourceOptions.map(s => s.value)));
  };

  const clearSources = () => {
    setSelectedSources(new Set());
  };

  // WebSocket for real-time updates
  useEffect(() => {
    const ws = createJobWebSocket((data) => {
      if (data.status === 'completed' || data.status === 'failed') {
        refetch();
        if (data.status === 'completed') {
          toast.success(data.message || 'Job completed');
        } else if (data.status === 'failed') {
          toast.error(data.message || 'Job failed');
        }
      }
    });

    return () => ws.close();
  }, [refetch]);

  const handleCreateJob = async () => {
    if (!query.trim()) {
      toast.error('Please enter a search query');
      return;
    }

    if (selectedSources.size === 0) {
      toast.error('Please select at least one source');
      return;
    }

    setIsSubmitting(true);
    
    try {
      // Create a job for each selected source
      const sources = Array.from(selectedSources);
      const promises = sources.map(source => 
        createJob.mutateAsync({
          source: source as any,
          query: query.trim(),
          max_reviews: parseInt(maxReviews) || 50,
          subreddits: source === 'reddit' ? subreddits : undefined,
        })
      );
      
      await Promise.all(promises);
      
      toast.success(`Started ${sources.length} scrape job${sources.length > 1 ? 's' : ''}`);
      setShowNewJob(false);
      setQuery('');
      refetch();
    } catch (e: any) {
      toast.error(e.message || 'Failed to start jobs');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = async (id: number) => {
    try {
      await cancelJob.mutateAsync(id);
      toast.success('Job cancelled');
    } catch (e: any) {
      toast.error(e.message || 'Failed to cancel job');
    }
  };

  const jobs = data?.jobs ?? [];
  const runningJobs = jobs.filter((j) => j.status === 'running' || j.status === 'pending');
  const completedJobs = jobs.filter((j) => j.status === 'completed' || j.status === 'failed');

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight">Scrape Jobs</h1>
          <p className="text-muted-foreground">
            {runningJobs.length > 0
              ? `${runningJobs.length} job(s) running`
              : 'No active jobs'}
          </p>
        </div>
        <div className="flex gap-3">
          <Button 
            variant="outline" 
            size="icon" 
            onClick={() => refetch()}
            className="rounded-xl border-border/50"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={showNewJob} onOpenChange={setShowNewJob}>
            <DialogTrigger asChild>
              <Button className="bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white shadow-lg shadow-indigo-500/25">
                <Plus className="mr-2 h-4 w-4" />
                New Scrape
              </Button>
            </DialogTrigger>
            <DialogContent className="rounded-2xl">
              <DialogHeader>
                <DialogTitle className="text-xl">Start New Scrape</DialogTitle>
                <DialogDescription>
                  Configure and start a new review scraping job
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-5 py-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">Sources</Label>
                    <div className="flex gap-2">
                      <Button 
                        type="button" 
                        variant="ghost" 
                        size="sm" 
                        onClick={selectAllSources}
                        className="h-7 text-xs text-muted-foreground hover:text-foreground"
                      >
                        Select all
                      </Button>
                      <Button 
                        type="button" 
                        variant="ghost" 
                        size="sm" 
                        onClick={clearSources}
                        className="h-7 text-xs text-muted-foreground hover:text-foreground"
                      >
                        Clear
                      </Button>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    {sourceOptions.map((opt) => {
                      const IconComponent = opt.icon;
                      const isSelected = selectedSources.has(opt.value);
                      return (
                        <label
                          key={opt.value}
                          className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-all ${
                            isSelected 
                              ? 'border-indigo-500/50 bg-indigo-500/5 dark:bg-indigo-500/10' 
                              : 'border-border/50 hover:border-border hover:bg-muted/50'
                          }`}
                        >
                          <Checkbox
                            checked={isSelected}
                            onCheckedChange={() => toggleSource(opt.value)}
                            className="mt-0.5 data-[state=checked]:bg-indigo-500 data-[state=checked]:border-indigo-500"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <IconComponent className={`h-4 w-4 ${opt.color}`} />
                              <span className="font-medium text-sm">{opt.label}</span>
                            </div>
                            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                              {opt.description}
                            </p>
                          </div>
                        </label>
                      );
                    })}
                  </div>
                  {selectedSources.size === 0 && (
                    <p className="text-xs text-destructive">Select at least one source</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium">Topic or Industry</Label>
                  <Input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g., roofing contractors, home renovation, HVAC maintenance"
                    className="h-11 rounded-xl border-border/50 bg-muted/50 focus:bg-background transition-colors"
                  />
                  <p className="text-xs text-muted-foreground">
                    Search for books about this topic across {selectedSources.size} source{selectedSources.size !== 1 ? 's' : ''}
                  </p>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium">Max Reviews per Source</Label>
                  <Input
                    type="number"
                    value={maxReviews}
                    onChange={(e) => setMaxReviews(e.target.value)}
                    min="1"
                    max="500"
                    className="h-11 rounded-xl border-border/50 bg-muted/50 focus:bg-background transition-colors"
                  />
                </div>

                {selectedSources.has('reddit') && (
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Subreddits (comma-separated)</Label>
                    <Input
                      value={subreddits}
                      onChange={(e) => setSubreddits(e.target.value)}
                      placeholder="books,suggestmeabook,productivity"
                      className="h-11 rounded-xl border-border/50 bg-muted/50 focus:bg-background transition-colors"
                    />
                  </div>
                )}
              </div>

              <DialogFooter className="gap-2">
                <Button 
                  variant="outline" 
                  onClick={() => setShowNewJob(false)}
                  className="rounded-xl border-border/50"
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleCreateJob} 
                  disabled={isSubmitting || selectedSources.size === 0}
                  className="rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white"
                >
                  {isSubmitting ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="mr-2 h-4 w-4" />
                  )}
                  Start {selectedSources.size} Scrape{selectedSources.size !== 1 ? 's' : ''}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Running Jobs */}
      {runningJobs.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Active Jobs</h2>
          <div className="space-y-3">
            {runningJobs.map((job) => (
              <JobCard key={job.id} job={job} onCancel={handleCancel} />
            ))}
          </div>
        </div>
      )}

      {/* Completed Jobs */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Job History</h2>
        {isLoading ? (
          <Card className="border-border/50 shadow-sm">
            <CardContent className="py-12 text-center text-muted-foreground">
              <Loader2 className="h-6 w-6 animate-spin mx-auto mb-3 text-indigo-500" />
              Loading jobs...
            </CardContent>
          </Card>
        ) : completedJobs.length === 0 && runningJobs.length === 0 ? (
          <Card className="border-border/50 shadow-sm">
            <CardContent className="py-8">
              <EmptyState
                icon={Rocket}
                title="Ready to scrape"
                description="Search for books about a topic or industry to aggregate reviews from Amazon, Goodreads, Reddit, or LibraryThing."
                actions={[
                  { label: 'Start First Scrape', onClick: () => setShowNewJob(true), icon: Plus },
                ]}
              />
            </CardContent>
          </Card>
        ) : completedJobs.length === 0 ? (
          <Card className="border-border/50 shadow-sm">
            <CardContent className="py-12 text-center text-muted-foreground">
              No completed jobs yet. Your running job will appear here when finished.
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {completedJobs.map((job) => (
              <JobCard key={job.id} job={job} onCancel={handleCancel} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
