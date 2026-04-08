import { Fragment } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { ProjectRecommendation } from '@/types/industryConnect';

interface ProjectCardProps {
  project: ProjectRecommendation;
}

/** Render inline markdown: **bold**, *italic*, `code` */
function InlineText({ text }: { text: string }) {
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;
  let last = 0;
  let match: RegExpExecArray | null;
  let key = 0;
  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) parts.push(<Fragment key={key++}>{text.slice(last, match.index)}</Fragment>);
    if (match[2]) parts.push(<strong key={key++} className="font-semibold">{match[2]}</strong>);
    else if (match[3]) parts.push(<em key={key++}>{match[3]}</em>);
    else if (match[4]) parts.push(<code key={key++} className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]">{match[4]}</code>);
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push(<Fragment key={key++}>{text.slice(last)}</Fragment>);
  return <>{parts}</>;
}

export default function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{project.project_title || 'Capstone Project'}</CardTitle>
        {project.objective && (
          <p className="text-sm text-muted-foreground italic">{project.objective}</p>
        )}
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="tech-stack">
          <TabsList>
            <TabsTrigger value="tech-stack">Tech Stack</TabsTrigger>
            <TabsTrigger value="steps">Implementation Steps</TabsTrigger>
          </TabsList>
          <TabsContent value="tech-stack" className="pt-4">
            {project.tech_stack && project.tech_stack.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {project.tech_stack.map((tech, i) => {
                  const clean = tech.replace(/^[-*>]\s*/, '').trim();
                  return clean ? (
                    <Badge key={i} variant="secondary">{clean}</Badge>
                  ) : null;
                })}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No specific tech stack listed.</p>
            )}
          </TabsContent>
          <TabsContent value="steps" className="pt-4">
            {project.implementation_steps && project.implementation_steps.length > 0 ? (
              <ol className="space-y-4">
                {project.implementation_steps.map((step, i) => {
                  // Strip leading numbering like "1." / "Step 1:" / "1)" / "**1."
                  const clean = step.replace(/^\*{0,2}(?:Step\s*)?\d+[.):\-]\s*\*{0,2}\s*/i, '').trim();
                  // Split into a title (up to first sentence / period / dash separator) and body
                  const dashIdx = clean.search(/\s[—–-]\s/);
                  const periodIdx = clean.indexOf('. ');
                  const splitAt = dashIdx !== -1 ? dashIdx : periodIdx !== -1 && periodIdx < 80 ? periodIdx : -1;

                  const title = splitAt !== -1 ? clean.slice(0, splitAt).trim() : null;
                  const body  = splitAt !== -1 ? clean.slice(splitAt).replace(/^[\s.—–-]+/, '').trim() : clean;

                  return (
                    <li key={i} className="text-sm leading-relaxed">
                      <div className="flex gap-2">
                        <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[11px] font-bold text-primary">
                          {i + 1}
                        </span>
                        <div>
                          {title && (
                            <p className="font-semibold text-foreground mb-0.5">
                              <InlineText text={title} />
                            </p>
                          )}
                          <p className="text-muted-foreground">
                            <InlineText text={body} />
                          </p>
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ol>
            ) : (
              <p className="text-sm text-muted-foreground">No steps available.</p>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
