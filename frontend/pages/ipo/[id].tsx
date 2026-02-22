// pages/ipo/[id].tsx - IPO Detail Page
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { apiService } from '@/services/api';

export default function IPODetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const [ipo, setIPO] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadIPO();
    }
  }, [id]);

  const loadIPO = async () => {
    try {
      setLoading(true);
      const data = await apiService.getIPOById(Number(id));
      setIPO(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="container mx-auto px-4 py-8">Loading...</div>;
  if (error) return <div className="container mx-auto px-4 py-8">Error: {error}</div>;
  if (!ipo) return <div className="container mx-auto px-4 py-8">IPO not found</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="card">
        <h1 className="text-3xl font-bold mb-4">{ipo.company_name}</h1>
        <p className="text-gray-600 mb-6">{ipo.symbol}</p>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">Issue Size</p>
            <p className="text-lg font-semibold">₹{ipo.issue_size_rs_cr} Cr</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Price Band</p>
            <p className="text-lg font-semibold">
              ₹{ipo.price_band_lower} - ₹{ipo.price_band_upper}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Status</p>
            <p className="text-lg font-semibold capitalize">{ipo.status}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Industry</p>
            <p className="text-lg font-semibold">{ipo.industry_sector}</p>
          </div>
        </div>

        <div className="mt-6">
          <button
            onClick={() => router.push(`/ipo/${id}/upload`)}
            className="btn-primary"
          >
            Upload Prospectus
          </button>
        </div>
      </div>
    </div>
  );
}
