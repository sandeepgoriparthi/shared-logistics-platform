import { MobileTrackingView } from "@/components/mobile/mobile-tracking-view"

export default function MobileTrackingPage({ params }: { params: { id: string } }) {
  return <MobileTrackingView shipmentId={params.id} />
}
