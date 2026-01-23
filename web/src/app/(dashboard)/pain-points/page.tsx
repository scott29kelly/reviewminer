'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { usePainPoints, useCategories, useStartAnalysis } from '@/lib/hooks';
import { api, PainPoint } from '@/lib/api';
import { toast } from 'sonner';
import {
  Search,
  Download,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  X,
  FileJson,
  FileText,
  FileSpreadsheet,
  AlertTriangle,
  Play,
  Flame,
  Zap,
  Leaf,
} from 'lucide-react';
import { EmptyState } from '@/components/empty-state';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

const intensityConfig = {
  high: { 
    color: 'bg-rose-500', 
    bgColor: 'bg-rose-500/10 dark:bg-rose-500/20',
    textColor: 'text-rose-600 dark:text-rose-400',
    label: 'High',
    icon: Flame,
  },
  medium: { 
    color: 'bg-amber-500', 
    bgColor: 'bg-amber-500/10 dark:bg-amber-500/20',
    textColor: 'text-amber-600 dark:text-amber-400',
    label: 'Medium',
    icon: Zap,
  },
  low: { 
    color: 'bg-emerald-500', 
    bgColor: 'bg-emerald-500/10 dark:bg-emerald-500/20',
    textColor: 'text-emerald-600 dark:text-emerald-400',
    label: 'Low',
    icon: Leaf,
  },
};

function PainPointCard({ painPoint }: { painPoint: PainPoint }) {
  const config = intensityConfig[painPoint.emotional_intensity] || intensityConfig.medium;
  const IntensityIcon = config.icon;

  return (
    <div className="group p-4 rounded-xl border border-border/50 bg-card hover:bg-accent/30 hover:border-border transition-all duration-200">
      <div className="flex items-start gap-4">
        <div className={`shrink-0 flex h-8 w-8 items-center justify-center rounded-lg ${config.bgColor}`}>
          <IntensityIcon className={`h-4 w-4 ${config.textColor}`} />
        </div>
        <div className="flex-1 min-w-0 space-y-2">
          <p className="text-sm leading-relaxed font-medium">
            &ldquo;{painPoint.verbatim_quote}&rdquo;
          </p>
          {painPoint.implied_need && (
            <p className="text-xs text-muted-foreground">
              <span className="font-semibold text-foreground/80">Implied need:</span> {painPoint.implied_need}
            </p>
          )}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <Badge 
              variant="outline" 
              className="rounded-lg text-xs capitalize bg-muted/50 border-border/50"
            >
              {painPoint.source}
            </Badge>
            {painPoint.product_title && (
              <span className="text-xs text-muted-foreground truncate max-w-[180px]">
                {painPoint.product_title}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function PainPointsPage() {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState<string>('');
  const [intensity, setIntensity] = useState<string>('');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  const { data: categories } = useCategories();
  const { data, isLoading, refetch } = usePainPoints({
    page: 1,
    page_size: 100,
    search: search || undefined,
    category: category || undefined,
    intensity: intensity || undefined,
  });
  
  const startAnalysis = useStartAnalysis();
  
  const handleAnalyze = async () => {
    try {
      const result = await startAnalysis.mutateAsync({ unprocessed_only: true });
      toast.success(result.message);
      refetch();
    } catch (e: any) {
      toast.error(e.message || 'Failed to start analysis');
    }
  };

  const painPoints = data?.pain_points ?? [];

  // Group by category
  const grouped = painPoints.reduce((acc, pp) => {
    if (!acc[pp.category]) acc[pp.category] = [];
    acc[pp.category].push(pp);
    return acc;
  }, {} as Record<string, PainPoint[]>);

  const sortedCategories = Object.entries(grouped).sort((a, b) => b[1].length - a[1].length);

  const toggleCategory = (cat: string) => {
    const newSet = new Set(expandedCategories);
    if (newSet.has(cat)) {
      newSet.delete(cat);
    } else {
      newSet.add(cat);
    }
    setExpandedCategories(newSet);
  };

  const expandAll = () => {
    setExpandedCategories(new Set(Object.keys(grouped)));
  };

  const collapseAll = () => {
    setExpandedCategories(new Set());
  };

  const clearFilters = () => {
    setSearch('');
    setCategory('');
    setIntensity('');
  };

  const hasFilters = search || category || intensity;

  const handleExport = (format: 'csv' | 'json' | 'markdown') => {
    const url = api.exportPainPoints(format, category || undefined);
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight">Pain Points</h1>
          <p className="text-muted-foreground">
            {data?.total ?? 0} pain points across {Object.keys(grouped).length} categories
          </p>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button className="bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white shadow-lg shadow-indigo-500/25">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="rounded-xl">
            <DropdownMenuItem onClick={() => handleExport('csv')} className="rounded-lg">
              <FileSpreadsheet className="mr-2 h-4 w-4" />
              Export as CSV
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleExport('json')} className="rounded-lg">
              <FileJson className="mr-2 h-4 w-4" />
              Export as JSON
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleExport('markdown')} className="rounded-lg">
              <FileText className="mr-2 h-4 w-4" />
              Export as Markdown
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Filters */}
      <Card className="border-border/50 shadow-sm">
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search pain points..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-10 h-11 rounded-xl border-border/50 bg-muted/50 focus:bg-background transition-colors"
                />
              </div>
            </div>

            <Select value={category || 'all'} onValueChange={(v) => setCategory(v === 'all' ? '' : v)}>
              <SelectTrigger className="w-[200px] h-11 rounded-xl border-border/50">
                <SelectValue placeholder="All categories" />
              </SelectTrigger>
              <SelectContent className="rounded-xl">
                <SelectItem value="all">All categories</SelectItem>
                {categories?.map((cat) => (
                  <SelectItem key={cat.category} value={cat.category}>
                    {cat.category} ({cat.count})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={intensity || 'all'} onValueChange={(v) => setIntensity(v === 'all' ? '' : v)}>
              <SelectTrigger className="w-[160px] h-11 rounded-xl border-border/50">
                <SelectValue placeholder="All intensity" />
              </SelectTrigger>
              <SelectContent className="rounded-xl">
                <SelectItem value="all">All intensity</SelectItem>
                <SelectItem value="high">
                  <span className="flex items-center gap-2">
                    <Flame className="h-3 w-3 text-rose-500" /> High
                  </span>
                </SelectItem>
                <SelectItem value="medium">
                  <span className="flex items-center gap-2">
                    <Zap className="h-3 w-3 text-amber-500" /> Medium
                  </span>
                </SelectItem>
                <SelectItem value="low">
                  <span className="flex items-center gap-2">
                    <Leaf className="h-3 w-3 text-emerald-500" /> Low
                  </span>
                </SelectItem>
              </SelectContent>
            </Select>

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

      {/* Actions */}
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={expandAll} className="rounded-xl border-border/50">
          Expand All
        </Button>
        <Button variant="outline" size="sm" onClick={collapseAll} className="rounded-xl border-border/50">
          Collapse All
        </Button>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-xl" />
          ))}
        </div>
      ) : painPoints.length === 0 ? (
        <Card className="border-border/50 shadow-sm">
          <CardContent className="py-8">
            <EmptyState
              icon={AlertTriangle}
              title="No pain points yet"
              description="Pain points are extracted when you analyze your collected reviews. Start by running analysis on your review data."
              actions={[
                { label: 'Run Analysis', onClick: handleAnalyze, icon: Play },
                { label: 'View Reviews', href: '/reviews', variant: 'outline' },
              ]}
            />
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {sortedCategories.map(([cat, items]) => {
            const highCount = items.filter((p) => p.emotional_intensity === 'high').length;
            const mediumCount = items.filter((p) => p.emotional_intensity === 'medium').length;
            const lowCount = items.filter((p) => p.emotional_intensity === 'low').length;

            return (
              <Collapsible
                key={cat}
                open={expandedCategories.has(cat)}
                onOpenChange={() => toggleCategory(cat)}
              >
                <Card className="border-border/50 shadow-sm overflow-hidden">
                  <CollapsibleTrigger asChild>
                    <CardHeader className="cursor-pointer hover:bg-accent/50 transition-colors py-5">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                            {expandedCategories.has(cat) ? (
                              <ChevronDown className="h-5 w-5 text-muted-foreground" />
                            ) : (
                              <ChevronRight className="h-5 w-5 text-muted-foreground" />
                            )}
                          </div>
                          <CardTitle className="text-lg font-semibold">{cat}</CardTitle>
                          <Badge variant="secondary" className="rounded-lg font-semibold">
                            {items.length}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-3">
                          {highCount > 0 && (
                            <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-rose-500/10">
                              <Flame className="h-3 w-3 text-rose-500" />
                              <span className="text-xs font-medium text-rose-600 dark:text-rose-400">
                                {highCount}
                              </span>
                            </div>
                          )}
                          {mediumCount > 0 && (
                            <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-amber-500/10">
                              <Zap className="h-3 w-3 text-amber-500" />
                              <span className="text-xs font-medium text-amber-600 dark:text-amber-400">
                                {mediumCount}
                              </span>
                            </div>
                          )}
                          {lowCount > 0 && (
                            <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-emerald-500/10">
                              <Leaf className="h-3 w-3 text-emerald-500" />
                              <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">
                                {lowCount}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <CardContent className="pt-0 pb-6">
                      <div className="grid gap-3 md:grid-cols-2">
                        {items.map((pp) => (
                          <PainPointCard key={pp.id} painPoint={pp} />
                        ))}
                      </div>
                    </CardContent>
                  </CollapsibleContent>
                </Card>
              </Collapsible>
            );
          })}
        </div>
      )}
    </div>
  );
}
