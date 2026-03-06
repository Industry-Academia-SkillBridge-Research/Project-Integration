import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Brain, Target, Sparkles, ChevronRight, BarChart3, Route, Lightbulb, User, LogOut } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Link } from "react-router-dom";

const Landing = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const features = [
    {
      icon: Brain,
      title: "AI-Powered Analysis",
      description: "Advanced agentic pipeline extracts and normalizes skills from candidate profiles using cutting-edge NLP.",
    },
    {
      icon: Target,
      title: "Skill Gap Detection",
      description: "Precisely identify gaps between current skills and target role requirements with explainable insights.",
    },
    {
      icon: Route,
      title: "Learning Paths",
      description: "Personalized learning recommendations to bridge skill gaps and accelerate career growth.",
    },
    {
      icon: Lightbulb,
      title: "Explainable AI",
      description: "Transparent reasoning behind every recommendation, ensuring trust and actionable insights.",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-hero">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent/5 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 right-1/3 w-64 h-64 bg-pipeline-normalize/5 rounded-full blur-3xl animate-float" style={{ animationDelay: '4s' }} />
      </div>

      {/* Header */}
      <header className="relative z-10 container mx-auto px-6 py-6">
        <nav className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-primary flex items-center justify-center shadow-glow">
              <BarChart3 className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-foreground">SkillScope</span>
          </div>
          <div className="flex items-center gap-3">
            {user ? (
              <>
                <Button variant="glass" onClick={() => navigate('/modules')}>
                  Dashboard
                  <ChevronRight className="w-4 h-4" />
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                      <Avatar>
                        <AvatarImage src={user.picture} alt={user.name} />
                        <AvatarFallback className="bg-primary text-primary-foreground">
                          {user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                        </AvatarFallback>
                      </Avatar>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <DropdownMenuLabel>
                      <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium leading-none">{user.name}</p>
                        <p className="text-xs leading-none text-muted-foreground">
                          {user.email}
                        </p>
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem asChild>
                      <Link to="/profile" className="cursor-pointer flex items-center">
                        <User className="mr-2 h-4 w-4" />
                        <span>Profile</span>
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={logout} className="cursor-pointer text-destructive">
                      <LogOut className="mr-2 h-4 w-4" />
                      <span>Sign Out</span>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <Button variant="glass" onClick={() => navigate('/auth')}>
                Get Started
                <ChevronRight className="w-4 h-4" />
              </Button>
            )}
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 container mx-auto px-6 pt-16 pb-24">
        <div className="max-w-4xl mx-auto text-center animate-slide-up">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary/50 border border-border mb-8">
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-sm text-muted-foreground">Research-Grade Employability Analysis</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            <span className="text-foreground">Explainable</span>
            <br />
            <span className="text-gradient-primary">Employability Analysis</span>
          </h1>
          
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
            Leverage AI-powered skill gap analysis with transparent reasoning to unlock personalized learning paths and career growth opportunities.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="hero" size="xl" onClick={() => navigate('/auth')}>
              Start Analysis
              <ChevronRight className="w-5 h-5" />
            </Button>
            <Button variant="outline" size="xl" onClick={() => navigate('/auth')}>
              View Demo
            </Button>
          </div>
        </div>

        {/* Pipeline Preview */}
        <div className="mt-24 max-w-5xl mx-auto animate-fade-in" style={{ animationDelay: '0.3s' }}>
          <div className="bg-gradient-card rounded-2xl border border-border p-8 shadow-elevated">
            <h3 className="text-lg font-semibold text-foreground mb-6 text-center">Agentic Pipeline Stages</h3>
            <div className="flex flex-wrap justify-center gap-4">
              {[
                { label: 'Extracting', gradient: 'pipeline-stage-1' },
                { label: 'Normalizing', gradient: 'pipeline-stage-2' },
                { label: 'Writing to Neo4j', gradient: 'pipeline-stage-3' },
                { label: 'Analyzing Gaps', gradient: 'pipeline-stage-4' },
                { label: 'Explanation', gradient: 'pipeline-stage-5' },
                { label: 'Recommendation', gradient: 'pipeline-stage-6' },
              ].map((stage, index) => (
                <div key={stage.label} className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${stage.gradient} animate-pulse-glow`} style={{ animationDelay: `${index * 0.2}s` }} />
                  <span className="text-sm text-muted-foreground">{stage.label}</span>
                  {index < 5 && <ChevronRight className="w-4 h-4 text-border" />}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-24 grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
          {features.map((feature, index) => (
            <div
              key={feature.title}
              className="bg-gradient-card rounded-xl border border-border p-6 shadow-card hover:shadow-elevated transition-all duration-300 hover:-translate-y-1 animate-scale-in"
              style={{ animationDelay: `${0.1 * index}s` }}
            >
              <div className="w-12 h-12 rounded-xl bg-secondary flex items-center justify-center mb-4">
                <feature.icon className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">{feature.title}</h3>
              <p className="text-sm text-muted-foreground">{feature.description}</p>
            </div>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-border py-8">
        <div className="container mx-auto px-6 text-center text-sm text-muted-foreground">
          <p>Explainable Employability Analysis & Learning Path Recommender</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
