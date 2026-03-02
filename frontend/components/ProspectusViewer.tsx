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

      if (!response.ok) throw 'Download failed';

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
      <div className="empty-state">
        <div className="empty-state-icon">
          <svg className="w-7 h-7 text-navy-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-navy-900 mb-2">No Prospectus Available</h3>
        <p className="text-navy-500 text-sm">No sections could be extracted from the prospectus</p>
      </div>
    );
  }

  const activeSectionData = sections.find(s => s.name === activeSection);

  return (
    <div className="space-y-4 sm:space-y-6">
      {metadata && (
        <div className="card">
          <div className="flex flex-col sm:flex-row items-start justify-between gap-4">
            <div className="flex-1">
              <h3 className="text-base sm:text-lg font-semibold text-navy-900 mb-3">
                Prospectus Information
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 text-sm">
                <div>
                  <p className="text-navy-500 text-xs sm:text-sm">Pages</p>
                  <p className="font-medium text-navy-900">{metadata.pdf_info?.page_count || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-navy-500 text-xs sm:text-sm">Words</p>
                  <p className="font-medium text-navy-900">{metadata.word_count?.toLocaleString() || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-navy-500 text-xs sm:text-sm">Sections</p>
                  <p className="font-medium text-navy-900">{sections.length}</p>
                </div>
                <div>
                  <p className="text-navy-500 text-xs sm:text-sm">Uploaded</p>
                  <p className="font-medium text-navy-900">
                    {metadata.created_at ? new Date(metadata.created_at).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
              </div>
            </div>
            <button
              onClick={downloadProspectus}
              className="btn-primary flex items-center gap-2 flex-shrink-0"
              aria-label={`Download prospectus for ${companyName}`}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="hidden xs:inline">Download PDF</span>
              <span className="xs:hidden">PDF</span>
            </button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border border-navy-100 shadow-card overflow-hidden">
        <div className="border-b border-navy-200 overflow-x-auto">
          <nav className="flex space-x-1 sm:space-x-4 px-3 sm:px-6" aria-label="Prospectus sections">
            {sections.map((section) => (
              <button
                key={section.name}
                onClick={() => setActiveSection(section.name)}
                role="tab"
                aria-selected={activeSection === section.name}
                className={`whitespace-nowrap py-3 sm:py-4 px-1 border-b-2 font-medium text-xs sm:text-sm transition-colors ${activeSection === section.name
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-navy-500 hover:text-navy-700 hover:border-navy-300'
                  }`}
              >
                {section.displayName}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-4 sm:p-6">
          {activeSectionData && (
            <div>
              <h3 className="text-lg sm:text-xl font-semibold text-navy-900 mb-3 sm:mb-4">
                {activeSectionData.displayName}
              </h3>
              <div className="whitespace-pre-wrap text-xs sm:text-sm text-navy-700 leading-relaxed">
                {activeSectionData.content || 'No content available for this section.'}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 sm:gap-4">
        {sections.map((section) => (
          <div key={section.name} className="stat-card text-center">
            <h4 className="text-2xs sm:text-xs font-medium text-navy-500 mb-1 truncate">
              {section.displayName}
            </h4>
            <p className="text-lg sm:text-2xl font-bold text-navy-900">
              {section.content.split(' ').length.toLocaleString()}
            </p>
            <p className="text-2xs sm:text-xs text-navy-400 mt-0.5">words</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProspectusViewer;
