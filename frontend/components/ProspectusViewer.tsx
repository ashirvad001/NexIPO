import React, { useState, useEffect } from 'react';
import { apiService } from '@/services/api';
import Loading from './Loading';
import Error from './Error';

interface ProspectusViewerProps {
  ipoId: number;
  companyName: string;
}

interface ProspectusSection {
  name: string;
  content: string;
  displayName: string;
}

const ProspectusViewer: React.FC<ProspectusViewerProps> = ({ ipoId, companyName }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sections, setSections] = useState<ProspectusSection[]>([]);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<any>(null);

  const sectionDisplayNames: Record<string, string> = {
    company_overview: 'Company Overview',
    risk_factors: 'Risk Factors',
    financial_information: 'Financial Information',
    management: 'Management & Board',
    objects_of_issue: 'Objects of Issue',
    industry_overview: 'Industry Overview',
    competitive_strengths: 'Competitive Strengths',
    business_strategy: 'Business Strategy',
  };

  const fetchProspectus = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.getProspectusSections(ipoId);
      
      if (response.sections && Object.keys(response.sections).length > 0) {
        const sectionsArray = Object.entries(response.sections).map(([name, content]) => ({
          name,
          content: content as string,
          displayName: sectionDisplayNames[name] || name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        }));
        
        setSections(sectionsArray);
        setActiveSection(sectionsArray[0]?.name || null);
        
        const prospectusData = await apiService.getProspectus(ipoId, false);
        setMetadata(prospectusData.prospectus);
      } else {
        setError('No sections found in prospectus');
      }
    } catch (err: any) {
      console.error('Error fetching prospectus:', err);
      setError(err.response?.data?.detail || 'Failed to load prospectus');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProspectus();
  }, [ipoId]);

  const downloadProspectus = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/files/download/prospectus/${ipoId}`
      );
      
      if (!response.ok) throw new Error('Download failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${companyName}_Prospectus.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Download error:', err);
      alert('Failed to download prospectus');
    }
  };

  if (loading) {
    return <Loading text="Loading prospectus..." />;
  }

  if (error) {
    return <Error message={error} retry={fetchProspectus} />;
  }

  if (sections.length === 0) {
    return (
      <div className="card text-center py-12">
        <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Prospectus Available</h3>
        <p className="text-gray-600">No sections could be extracted from the prospectus</p>
      </div>
    );
  }

  const activeSectionData = sections.find(s => s.name === activeSection);

  return (
    <div className="space-y-6">
      {metadata && (
        <div className="card">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Prospectus Information
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Pages</p>
                  <p className="font-medium">{metadata.pdf_info?.page_count || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Words</p>
                  <p className="font-medium">{metadata.word_count?.toLocaleString() || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Sections</p>
                  <p className="font-medium">{sections.length}</p>
                </div>
                <div>
                  <p className="text-gray-500">Uploaded</p>
                  <p className="font-medium">
                    {metadata.created_at ? new Date(metadata.created_at).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
              </div>
            </div>
            <button
              onClick={downloadProspectus}
              className="btn-primary flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Download PDF
            </button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-card overflow-hidden">
        <div className="border-b border-gray-200 overflow-x-auto">
          <nav className="flex space-x-4 px-6" aria-label="Tabs">
            {sections.map((section) => (
              <button
                key={section.name}
                onClick={() => setActiveSection(section.name)}
                className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeSection === section.name
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {section.displayName}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeSectionData && (
            <div className="prose prose-sm max-w-none">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                {activeSectionData.displayName}
              </h3>
              <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                {activeSectionData.content || 'No content available for this section.'}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {sections.map((section) => (
          <div key={section.name} className="card">
            <h4 className="text-sm font-medium text-gray-500 mb-2">
              {section.displayName}
            </h4>
            <p className="text-2xl font-bold text-gray-900">
              {section.content.split(' ').length.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500 mt-1">words</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProspectusViewer;
