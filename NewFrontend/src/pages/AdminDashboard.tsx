import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Shield,
  Users,
  TrendingUp,
  Activity,
  Clock,
  UserCheck,
  LogOut,
  Search,
  Eye,
  Ban,
  CheckCircle,
  Trash2,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";

const AUTH_API_URL = import.meta.env.VITE_AUTH_API ||  'http://localhost:8182';

interface Admin {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_superadmin: boolean;
  last_login?: string;
}

interface DashboardStats {
  total_users: number;
  total_candidates: number;
  active_analyses: number;
  pending_processing: number;
  recent_registrations: number;
}

interface User {
  id: number;
  name: string;
  email: string;
  provider: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [admin, setAdmin] = useState<Admin | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [usersLoading, setUsersLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  const getAuthHeaders = () => {
    const token = localStorage.getItem("admin_token");
    if (!token) {
      navigate("/admin/login");
      return null;
    }
    return {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  };

  const fetchAdminInfo = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers) return;

      const response = await fetch(`${AUTH_API_URL}/admin/me`, { headers });
      if (!response.ok) {
        throw new Error("Session expired");
      }

      const data = await response.json();
      setAdmin(data.admin);
    } catch (error) {
      console.error("Failed to fetch admin info:", error);
      toast.error("Session expired. Please login again.");
      handleLogout();
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers) return;

      const response = await fetch(`${AUTH_API_URL}/admin/dashboard/stats`, { headers });
      if (!response.ok) throw new Error("Failed to fetch stats");

      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
      toast.error("Failed to load statistics");
    } finally {
      setStatsLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const headers = getAuthHeaders();
      if (!headers) return;

      const url = searchQuery
        ? `${AUTH_API_URL}/admin/users?search=${encodeURIComponent(searchQuery)}&limit=100`
        : `${AUTH_API_URL}/admin/users?limit=100`;

      const response = await fetch(url, { headers });
      if (!response.ok) throw new Error("Failed to fetch users");

      const data = await response.json();
      setUsers(data.users);
    } catch (error) {
      console.error("Failed to fetch users:", error);
      toast.error("Failed to load users");
    } finally {
      setUsersLoading(false);
    }
  };

  const handleToggleUserStatus = async (userId: number, currentStatus: boolean) => {
    try {
      const headers = getAuthHeaders();
      if (!headers) return;

      const response = await fetch(`${AUTH_API_URL}/admin/users/${userId}/toggle-active`, {
        method: "PATCH",
        headers,
      });

      if (!response.ok) throw new Error("Failed to update user status");

      const data = await response.json();
      toast.success(data.message);
      fetchUsers(); // Refresh user list
    } catch (error) {
      console.error("Failed to toggle user status:", error);
      toast.error("Failed to update user status");
    }
  };

  const handleDeleteUser = async (userId: number, userName: string) => {
    if (!confirm(`Are you sure you want to delete user "${userName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      const headers = getAuthHeaders();
      if (!headers) return;

      const response = await fetch(`${AUTH_API_URL}/admin/users/${userId}`, {
        method: "DELETE",
        headers,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete user");
      }

      toast.success("User deleted successfully");
      fetchUsers(); // Refresh user list
      fetchStats(); // Refresh stats
    } catch (error: any) {
      console.error("Failed to delete user:", error);
      toast.error(error.message || "Failed to delete user");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("admin_token");
    localStorage.removeItem("admin_user");
    navigate("/admin/login");
  };

  useEffect(() => {
    fetchAdminInfo();
    fetchStats();
    fetchUsers();
  }, []);

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      setUsersLoading(true);
      fetchUsers();
    }, 500);

    return () => clearTimeout(delayDebounce);
  }, [searchQuery]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <Loader2 className="w-12 h-12 text-cyan-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-gradient-to-br from-cyan-500 to-blue-600 p-3 rounded-xl">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
                <p className="text-sm text-slate-400">
                  Welcome back, {admin?.full_name || admin?.username}
                  {admin?.is_superadmin && (
                    <Badge variant="secondary" className="ml-2 bg-cyan-600 text-white text-xs">
                      Superadmin
                    </Badge>
                  )}
                </p>
              </div>
            </div>
            <Button
              variant="outline"
              onClick={handleLogout}
              className="border-slate-700 hover:bg-slate-800 text-slate-300"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          {statsLoading ? (
            <div className="col-span-full flex justify-center py-12">
              <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
            </div>
          ) : (
            <>
              <Card className="bg-slate-900/50 border-slate-800">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">Total Users</p>
                      <p className="text-3xl font-bold text-white">{stats?.total_users || 0}</p>
                    </div>
                    <Users className="w-10 h-10 text-cyan-400" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-900/50 border-slate-800">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">Total Candidates</p>
                      <p className="text-3xl font-bold text-white">{stats?.total_candidates || 0}</p>
                    </div>
                    <UserCheck className="w-10 h-10 text-blue-400" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-900/50 border-slate-800">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">Active Analyses</p>
                      <p className="text-3xl font-bold text-white">{stats?.active_analyses || 0}</p>
                    </div>
                    <Activity className="w-10 h-10 text-green-400" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-900/50 border-slate-800">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">Pending Processing</p>
                      <p className="text-3xl font-bold text-white">{stats?.pending_processing || 0}</p>
                    </div>
                    <Clock className="w-10 h-10 text-yellow-400" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-900/50 border-slate-800">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">New (7 days)</p>
                      <p className="text-3xl font-bold text-white">{stats?.recent_registrations || 0}</p>
                    </div>
                    <TrendingUp className="w-10 h-10 text-purple-400" />
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>

        {/* Users Table */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-white">User Management</CardTitle>
                <CardDescription className="text-slate-400">
                  View and manage all registered users
                </CardDescription>
              </div>
              <div className="relative w-64">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                <Input
                  type="text"
                  placeholder="Search users..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {usersLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
              </div>
            ) : users.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                No users found
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="border-slate-800 hover:bg-slate-800/50">
                      <TableHead className="text-slate-300">ID</TableHead>
                      <TableHead className="text-slate-300">Name</TableHead>
                      <TableHead className="text-slate-300">Email</TableHead>
                      <TableHead className="text-slate-300">Provider</TableHead>
                      <TableHead className="text-slate-300">Status</TableHead>
                      <TableHead className="text-slate-300">Joined</TableHead>
                      <TableHead className="text-slate-300 text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((user) => (
                      <TableRow key={user.id} className="border-slate-800 hover:bg-slate-800/30">
                        <TableCell className="text-slate-300">{user.id}</TableCell>
                        <TableCell className="text-slate-300">{user.name || "N/A"}</TableCell>
                        <TableCell className="text-slate-300">{user.email}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="border-slate-700 text-slate-300">
                            {user.provider}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {user.is_active ? (
                            <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Active
                            </Badge>
                          ) : (
                            <Badge variant="destructive">
                              <Ban className="w-3 h-3 mr-1" />
                              Inactive
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-slate-400 text-sm">
                          {new Date(user.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => navigate(`/admin/users/${user.id}`)}
                              className="text-cyan-400 hover:text-cyan-300 hover:bg-cyan-400/10"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleToggleUserStatus(user.id, user.is_active)}
                              className={user.is_active 
                                ? "text-yellow-400 hover:text-yellow-300 hover:bg-yellow-400/10" 
                                : "text-green-400 hover:text-green-300 hover:bg-green-400/10"
                              }
                            >
                              {user.is_active ? <Ban className="w-4 h-4" /> : <CheckCircle className="w-4 h-4" />}
                            </Button>
                            {admin?.is_superadmin && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeleteUser(user.id, user.name)}
                                className="text-red-400 hover:text-red-300 hover:bg-red-400/10"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminDashboard;
