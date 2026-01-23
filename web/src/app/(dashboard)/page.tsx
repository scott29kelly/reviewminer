'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { StatsCard } from '@/components/stats-card';
import { CategoryChart } from '@/components/charts/category-chart';
import { IntensityChart } from '@/components/charts/intensity-chart';
import { SourceChart } from '@/components/charts/source-chart';
import { useDashboard, useStartAnalysis } from '@/lib/hooks';
import {
  MessageSquareText,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Play,
  Download,
  RefreshCw,
  Upload,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { EmptyState } from '@/components/empty-state';
import Link from 'next/link';
import { toast } from 'sonner';

function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="border-border/50">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="space-y-3">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-8 w-20" />
                  <Skeleton className="h-3 w-32" />
                </div>
                <Skeleton className="h-12 w-12 rounded-xl" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2 border-border/50">
          <CardHeader>
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-4 w-56" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-[320px]" />
          </CardContent>
        </Card>
        <Card className="border-border/50">
          <CardHeader>
            <Skeleton className="h-5 w-32" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-[320px]" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function DashboardEmptyState() {
  return (
    <EmptyState
      icon={MessageSquareText}
      title="No reviews yet"
      description="Get started by searching for books about a topic or industry (e.g., 'roofing contractors', 'home renovation') to aggregate reviews and extract pain points."
      actions={[
        { label: 'Start Scraping', href: '/jobs', icon: Play },
        { label: 'Import CSV', href: '/reviews', variant: 'outline', icon: Upload },
      ]}
    />
  );
}

export default function DashboardPage() {
  const { data, isLoading, error, refetch } = useDashboard();
  const startAnalysis = useStartAnalysis();

  const handleAnalyze = async () => {
    try {
      const result = await startAnalysis.mutateAsync({ unprocessed_only: true });
      toast.success(result.message);
    } catch (e: any) {
      toast.error(e.message || 'Failed to start analysis');
    }
  };

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="text-center space-y-4">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
            <AlertTriangle className="h-8 w-8 text-destructive" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Failed to load dashboard</h3>
            <p className="text-sm text-muted-foreground">Please check your connection and try again.</p>
          </div>
          <Button onClick={() => refetch()} variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!data || data.reviews.total_reviews === 0) {
    return <DashboardEmptyState />;
  }

  const processedPercent = Math.round((data.reviews.processed_count / data.reviews.total_reviews) * 100);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your review analysis pipeline
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          {data.reviews.unprocessed_count > 0 && (
            <Button 
              onClick={handleAnalyze} 
              disabled={startAnalysis.isPending}
              className="bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white shadow-lg shadow-indigo-500/25"
            >
              {startAnalysis.isPending ? (
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="mr-2 h-4 w-4" />
              )}
              Analyze {data.reviews.unprocessed_count} Reviews
            </Button>
          )}
          <Button variant="outline" asChild className="border-border/50">
            <Link href="/pain-points">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Link>
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Reviews"
          value={data.reviews.total_reviews}
          icon={MessageSquareText}
          description={`From ${Object.keys(data.reviews.by_source).length} sources`}
          variant="primary"
        />
        <StatsCard
          title="Pain Points"
          value={data.pain_points.total_pain_points}
          icon={AlertTriangle}
          description={`${Object.keys(data.pain_points.by_category).length} categories`}
          variant="warning"
        />
        <StatsCard
          title="Processed"
          value={data.reviews.processed_count}
          icon={CheckCircle2}
          description={`${processedPercent}% complete`}
          variant="success"
        />
        <StatsCard
          title="Pending"
          value={data.reviews.unprocessed_count}
          icon={Clock}
          description="Awaiting analysis"
          variant={data.reviews.unprocessed_count > 0 ? 'danger' : 'default'}
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2 border-border/50 shadow-sm">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl">Pain Points by Category</CardTitle>
                <CardDescription className="mt-1">Top issues identified in customer reviews</CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild className="text-muted-foreground hover:text-foreground">
                <Link href="/pain-points">
                  View all
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent className="h-[320px] pb-6">
            <CategoryChart data={data.pain_points.by_category} />
          </CardContent>
        </Card>

        <Card className="border-border/50 shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl">Emotional Intensity</CardTitle>
            <CardDescription className="mt-1">Severity distribution</CardDescription>
          </CardHeader>
          <CardContent className="h-[320px] pb-6">
            <IntensityChart data={data.pain_points.by_intensity} />
          </CardContent>
        </Card>
      </div>

      {/* Source Distribution & Recent Activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-border/50 shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl">Reviews by Source</CardTitle>
            <CardDescription className="mt-1">Distribution across platforms</CardDescription>
          </CardHeader>
          <CardContent className="h-[280px] pb-6">
            <SourceChart data={data.reviews.by_source} />
          </CardContent>
        </Card>

        <Card className="border-border/50 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-4">
            <div>
              <CardTitle className="text-xl">Recent Pain Points</CardTitle>
              <CardDescription className="mt-1">Latest extracted insights</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild className="text-muted-foreground hover:text-foreground">
              <Link href="/pain-points">
                View all
                <ArrowRight className="ml-1 h-4 w-4" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {data.recent_pain_points.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-4">
                  <AlertTriangle className="h-6 w-6 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground">
                  No pain points extracted yet.<br />Run analysis to get started.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {data.recent_pain_points.slice(0, 5).map((pp: any) => (
                  <div 
                    key={pp.id} 
                    className="flex items-start gap-4 p-3 rounded-lg bg-muted/50 hover:bg-muted/80 transition-colors"
                  >
                    <Badge
                      variant={
                        pp.emotional_intensity === 'high'
                          ? 'destructive'
                          : pp.emotional_intensity === 'medium'
                          ? 'default'
                          : 'secondary'
                      }
                      className="mt-0.5 shrink-0 font-medium"
                    >
                      {pp.emotional_intensity}
                    </Badge>
                    <div className="flex-1 min-w-0 space-y-1">
                      <p className="text-sm font-semibold text-foreground">{pp.category}</p>
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        &ldquo;{pp.verbatim_quote}&rdquo;
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
