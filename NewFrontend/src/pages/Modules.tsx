import { Brain, Mic, TrendingUp, Link as LinkIcon } from "lucide-react";
import ModuleCard from "@/components/ModuleCard";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { ChevronLeft } from "lucide-react";

const Modules = () => {
  const modules = [
    {
      title: "Personalized Learning Path",
      description: "AI-driven recommendations tailored to your skills, goals, and industry requirements for optimal career growth.",
      icon: Brain,
      features: [
        "Adaptive learning algorithms",
        "Skill gap analysis",
        "Custom curriculum generation",
        "Progress tracking & analytics"
      ],
      link: "/analysis",
      gradient: "bg-gradient-primary"
    },
    {
      title: "Voice Bot Interview Prep",
      description: "Practice interviews with our AI voice assistant that provides real-time feedback and personalized coaching.",
      icon: Mic,
      features: [
        "Real-time voice interaction",
        "Industry-specific scenarios",
        "Instant feedback & scoring",
        "Performance improvement tips"
      ],
      link: "/interview-prep",
      gradient: "bg-gradient-accent"
    },
    {
      title: "Skill Gap Analysis",
      description: "Comprehensive assessment of your current skills versus industry demands with actionable improvement plans.",
      icon: TrendingUp,
      features: [
        "Current skill evaluation",
        "Industry benchmark comparison",
        "Priority skill recommendations",
        "Learning resource suggestions"
      ],
      link: "/skill-gap-analysis",
      gradient: "pipeline-stage-2"
    },
    {
      title: "Industry Connect Portal",
      description: "Connect directly with industry professionals, mentors, and companies for networking and opportunities.",
      icon: LinkIcon,
      features: [
        "Professional networking",
        "Mentor matching system",
        "Job opportunity alerts",
        "Collaboration projects"
      ],
      link: "/industry-connect",
      gradient: "bg-gradient-to-br from-accent to-primary"
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/50 backdrop-blur-sm bg-background/80 sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/">
              <h2 className="text-2xl font-bold text-gradient-primary">
                SkillScope
              </h2>
            </Link>
            <Link to="/">
              <Button variant="ghost" size="sm">
                <ChevronLeft className="w-4 h-4 mr-2" />
                Back to Home
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-20 bg-gradient-hero overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-20 right-10 w-32 h-32 bg-primary/10 rounded-full blur-2xl" />
          <div className="absolute bottom-20 left-10 w-40 h-40 bg-secondary/10 rounded-full blur-2xl" />
        </div>
        
        <div className="container mx-auto px-4 relative z-10">
          <div className="max-w-3xl mx-auto text-center space-y-6 animate-fade-in">
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground">
              Explore Our <span className="text-gradient-primary">Learning Modules</span>
            </h1>
            <p className="text-lg text-muted-foreground">
              Four integrated modules designed to accelerate your professional growth
              and bridge the gap between your current skills and industry requirements.
            </p>
          </div>
        </div>
      </section>

      {/* Modules Grid */}
      <section id="modules" className="py-20">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-7xl mx-auto">
            {modules.map((module, index) => (
              <div
                key={module.title}
                className="animate-slide-up"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <ModuleCard {...module} />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/50 py-8 bg-muted/30">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>© 2026 SkillScope - AI-powered employability analysis platform.</p>
        </div>
      </footer>
    </div>
  );
};

export default Modules;
