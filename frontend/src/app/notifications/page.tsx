import { DealNotifications } from "@/components/DealNotifications";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";
import { getDealAlerts } from "@/lib/api";

export default async function NotificationsPage() {
  const feed = await getDealAlerts(50);
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar title="Мэдэгдэл" />
        <main className="bg-surface-page p-8">
          <DealNotifications initialFeed={feed} />
        </main>
      </div>
    </div>
  );
}
