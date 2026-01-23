'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Settings, Database, Trash2, Download, AlertTriangle, Sparkles, Globe, BookOpen, MessageSquare, Library } from 'lucide-react';
import { toast } from 'sonner';

export default function SettingsPage() {
  const [scraperSettings, setScraperSettings] = useState({
    amazon: { enabled: true, delayMin: 3, delayMax: 7 },
    goodreads: { enabled: true, delayMin: 2, delayMax: 4 },
    reddit: { enabled: true },
    librarything: { enabled: true, delayMin: 2, delayMax: 5 },
  });

  const [analysisSettings, setAnalysisSettings] = useState({
    batchSize: 20,
    model: 'claude-sonnet-4-5-20250929',
  });

  const handleBackup = async () => {
    toast.info('Database backup feature coming soon');
  };

  const handleReset = async () => {
    toast.info('Database reset feature coming soon');
  };

  const sourceConfig = [
    { key: 'amazon', label: 'Amazon', description: 'Scrape book reviews from Amazon', icon: Globe },
    { key: 'goodreads', label: 'Goodreads', description: 'Scrape reviews from Goodreads book pages', icon: BookOpen },
    { key: 'reddit', label: 'Reddit', description: 'Search Reddit for book discussions', icon: MessageSquare },
    { key: 'librarything', label: 'LibraryThing', description: 'Scrape reviews from LibraryThing', icon: Library },
  ];

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Configure scraping, analysis, and database options
        </p>
      </div>

      {/* Scraper Settings */}
      <Card className="border-border/50 shadow-sm">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/10 dark:bg-indigo-500/20">
              <Settings className="h-5 w-5 text-indigo-500" />
            </div>
            <div>
              <CardTitle className="text-lg">Scraper Configuration</CardTitle>
              <CardDescription className="mt-0.5">
                Enable/disable sources and configure request delays
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-1">
          {sourceConfig.map((source, index) => {
            const SourceIcon = source.icon;
            const setting = scraperSettings[source.key as keyof typeof scraperSettings];
            
            return (
              <div key={source.key}>
                <div className="flex items-center justify-between py-4">
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-muted">
                      <SourceIcon className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div className="space-y-0.5">
                      <Label className="text-base font-semibold">{source.label}</Label>
                      <p className="text-sm text-muted-foreground">
                        {source.description}
                      </p>
                    </div>
                  </div>
                  <Switch
                    checked={setting.enabled}
                    onCheckedChange={(checked) =>
                      setScraperSettings({
                        ...scraperSettings,
                        [source.key]: { ...setting, enabled: checked },
                      })
                    }
                    className="data-[state=checked]:bg-indigo-500"
                  />
                </div>
                {index < sourceConfig.length - 1 && <Separator className="bg-border/50" />}
              </div>
            );
          })}
        </CardContent>
      </Card>

      {/* Analysis Settings */}
      <Card className="border-border/50 shadow-sm">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/10 dark:bg-violet-500/20">
              <Sparkles className="h-5 w-5 text-violet-500" />
            </div>
            <div>
              <CardTitle className="text-lg">Analysis Configuration</CardTitle>
              <CardDescription className="mt-0.5">
                Configure AI-powered pain point extraction
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Batch Size</Label>
              <Input
                type="number"
                value={analysisSettings.batchSize}
                onChange={(e) =>
                  setAnalysisSettings({
                    ...analysisSettings,
                    batchSize: parseInt(e.target.value) || 20,
                  })
                }
                min="1"
                max="50"
                className="h-11 rounded-xl border-border/50 bg-muted/50 focus:bg-background transition-colors"
              />
              <p className="text-xs text-muted-foreground">
                Number of reviews to analyze per API call
              </p>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Model</Label>
              <Input 
                value={analysisSettings.model} 
                disabled 
                className="h-11 rounded-xl border-border/50 bg-muted/30 font-mono text-sm"
              />
              <p className="text-xs text-muted-foreground">
                Claude model used for analysis
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Database Management */}
      <Card className="border-border/50 shadow-sm">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 dark:bg-emerald-500/20">
              <Database className="h-5 w-5 text-emerald-500" />
            </div>
            <div>
              <CardTitle className="text-lg">Database Management</CardTitle>
              <CardDescription className="mt-0.5">
                Backup or reset your database
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex flex-wrap gap-3">
            <Button 
              variant="outline" 
              onClick={handleBackup}
              className="rounded-xl border-border/50"
            >
              <Download className="mr-2 h-4 w-4" />
              Create Backup
            </Button>

            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button 
                  variant="destructive"
                  className="rounded-xl shadow-lg shadow-destructive/25"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Reset Database
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent className="rounded-2xl">
                <AlertDialogHeader>
                  <AlertDialogTitle className="flex items-center gap-3 text-xl">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-destructive/10">
                      <AlertTriangle className="h-5 w-5 text-destructive" />
                    </div>
                    Reset Database?
                  </AlertDialogTitle>
                  <AlertDialogDescription className="text-base">
                    This action cannot be undone. This will permanently delete all reviews,
                    pain points, and job history from your database.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter className="gap-2">
                  <AlertDialogCancel className="rounded-xl border-border/50">
                    Cancel
                  </AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleReset}
                    className="rounded-xl bg-destructive text-destructive-foreground hover:bg-destructive/90 shadow-lg shadow-destructive/25"
                  >
                    Yes, Reset Everything
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
          <p className="text-xs text-muted-foreground font-mono bg-muted/50 px-3 py-2 rounded-lg inline-block">
            data/review_miner.db
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
