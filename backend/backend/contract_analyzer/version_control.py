# version_control.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import difflib
import json
import logging
from enum import Enum

class VersionStatus(Enum):
    """Contract version status"""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"

@dataclass
class ContractSection:
    """Contract section representation"""
    name: str
    content: str
    order: int
    metadata: Dict[str, Any]

@dataclass
class ContractVersion:
    """Contract version metadata"""
    version_id: str
    content: str
    version_number: int
    timestamp: str
    author: str
    changes: Dict[str, Any]
    comments: str
    status: str
    previous_version: Optional[str]
    sections: Optional[List[ContractSection]] = None

@dataclass
class ContractDiff:
    """Contract version differences"""
    additions: List[str]
    deletions: List[str]
    modifications: List[Tuple[str, str]]
    similarity_score: float
    section_changes: Dict[str, Dict[str, Any]]

class ContractVersionManager:
    """Manages contract versioning and comparisons"""
    
    def __init__(self, vector_db):
        self.vector_db = vector_db
        self.logger = logging.getLogger(__name__)

    def create_version(
        self,
        contract_id: str,
        content: str,
        author: str,
        comments: str,
        status: str = "draft"
    ) -> Optional[ContractVersion]:
        """
        Create a new version of a contract
        
        Args:
            contract_id: Unique contract identifier
            content: Contract content
            author: Author creating the version
            comments: Version comments
            status: Version status
            
        Returns:
            ContractVersion if successful, None otherwise
        """
        try:
            # Get existing versions
            versions = self.get_version_history(contract_id)
            version_number = len(versions) + 1
            previous_version = versions[-1].version_id if versions else None
            
            # Process sections
            sections = self._extract_sections(content)
            
            # Create version metadata
            version = ContractVersion(
                version_id=f"{contract_id}_v{version_number}",
                content=content,
                version_number=version_number,
                timestamp=datetime.now().isoformat(),
                author=author,
                changes=self._compute_changes(content, versions[-1].content if versions else ""),
                comments=comments,
                status=status,
                previous_version=previous_version,
                sections=sections
            )
            
            # Store in database
            success = self.vector_db.store_contract_version(
                contract_id,
                content,
                self._version_to_metadata(version)
            )
            
            return version if success else None
            
        except Exception as e:
            self.logger.error(f"Failed to create version: {str(e)}")
            return None

    def get_version_history(self, contract_id: str) -> List[ContractVersion]:
        """Get complete version history"""
        try:
            versions = self.vector_db.get_contract_versions(contract_id)
            return [
                self._metadata_to_version(v['metadata'], v['content'])
                for v in versions
            ]
        except Exception as e:
            self.logger.error(f"Failed to get version history: {str(e)}")
            return []

    def compare_versions(
        self,
        contract_id: str,
        version1: int,
        version2: int
    ) -> Optional[ContractDiff]:
        """Compare two versions of a contract"""
        try:
            versions = self.get_version_history(contract_id)
            
            v1 = next((v for v in versions if v.version_number == version1), None)
            v2 = next((v for v in versions if v.version_number == version2), None)
            
            if not v1 or not v2:
                raise ValueError("Specified versions not found")
            
            # Compare full content
            diff = difflib.ndiff(
                v1.content.splitlines(keepends=True),
                v2.content.splitlines(keepends=True)
            )
            
            additions = []
            deletions = []
            modifications = []
            
            for line in diff:
                if line.startswith('+ '):
                    additions.append(line[2:])
                elif line.startswith('- '):
                    deletions.append(line[2:])
                elif line.startswith('? '):
                    continue
            
            # Compare sections
            section_changes = self._compare_sections(
                v1.sections or [],
                v2.sections or []
            )
            
            # Calculate similarity
            similarity = difflib.SequenceMatcher(
                None, v1.content, v2.content
            ).ratio()
            
            return ContractDiff(
                additions=additions,
                deletions=deletions,
                modifications=modifications,
                similarity_score=similarity,
                section_changes=section_changes
            )
            
        except Exception as e:
            self.logger.error(f"Failed to compare versions: {str(e)}")
            return None

    def analyze_changes(
        self,
        contract_id: str,
        version_number: int
    ) -> Dict[str, Any]:
        """Analyze changes in a specific version"""
        try:
            versions = self.get_version_history(contract_id)
            current = next(
                (v for v in versions if v.version_number == version_number), 
                None
            )
            
            if not current:
                raise ValueError(f"Version {version_number} not found")
            
            previous = next(
                (v for v in versions if v.version_number == version_number - 1),
                None
            )
            
            analysis = {
                'version_info': {
                    'number': current.version_number,
                    'author': current.author,
                    'timestamp': current.timestamp,
                    'status': current.status
                },
                'changes': current.changes,
                'section_analysis': self._analyze_section_changes(
                    previous.sections if previous else [],
                    current.sections or []
                ),
                'risk_factors': self._identify_risk_factors(current.content)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze changes: {str(e)}")
            return {}

    def _extract_sections(self, content: str) -> List[ContractSection]:
        """Extract sections from contract content"""
        try:
            sections = []
            current_section = None
            current_content = []
            order = 0
            
            for line in content.splitlines():
                if self._is_section_header(line):
                    if current_section:
                        sections.append(ContractSection(
                            name=current_section,
                            content='\n'.join(current_content),
                            order=order,
                            metadata={'type': 'standard'}
                        ))
                        order += 1
                        current_content = []
                    current_section = line.strip()
                else:
                    current_content.append(line)
            
            if current_section and current_content:
                sections.append(ContractSection(
                    name=current_section,
                    content='\n'.join(current_content),
                    order=order,
                    metadata={'type': 'standard'}
                ))
            
            return sections
            
        except Exception as e:
            self.logger.error(f"Failed to extract sections: {str(e)}")
            return []

    def _is_section_header(self, line: str) -> bool:
        """Check if line is a section header"""
        return (
            line.isupper() and 
            len(line.split()) <= 5 and 
            len(line.strip()) > 0
        )

    def _compare_sections(
        self,
        sections1: List[ContractSection],
        sections2: List[ContractSection]
    ) -> Dict[str, Dict[str, Any]]:
        """Compare sections between versions"""
        try:
            changes = {}
            sections1_dict = {s.name: s for s in sections1}
            sections2_dict = {s.name: s for s in sections2}
            
            for name in set(sections1_dict.keys()) | set(sections2_dict.keys()):
                if name not in sections1_dict:
                    changes[name] = {
                        'type': 'added',
                        'content': sections2_dict[name].content
                    }
                elif name not in sections2_dict:
                    changes[name] = {
                        'type': 'removed',
                        'content': sections1_dict[name].content
                    }
                else:
                    similarity = difflib.SequenceMatcher(
                        None,
                        sections1_dict[name].content,
                        sections2_dict[name].content
                    ).ratio()
                    
                    if similarity < 1.0:
                        changes[name] = {
                            'type': 'modified',
                            'similarity': similarity,
                            'old_content': sections1_dict[name].content,
                            'new_content': sections2_dict[name].content
                        }
            
            return changes
            
        except Exception as e:
            self.logger.error(f"Failed to compare sections: {str(e)}")
            return {}

    def _analyze_section_changes(
        self,
        old_sections: List[ContractSection],
        new_sections: List[ContractSection]
    ) -> Dict[str, Any]:
        """Analyze changes between sections"""
        try:
            analysis = {
                'added': [],
                'removed': [],
                'modified': [],
                'unchanged': []
            }
            
            old_dict = {s.name: s for s in old_sections}
            new_dict = {s.name: s for s in new_sections}
            
            for name in set(old_dict.keys()) | set(new_dict.keys()):
                if name not in old_dict:
                    analysis['added'].append(name)
                elif name not in new_dict:
                    analysis['removed'].append(name)
                else:
                    similarity = difflib.SequenceMatcher(
                        None,
                        old_dict[name].content,
                        new_dict[name].content
                    ).ratio()
                    
                    if similarity == 1.0:
                        analysis['unchanged'].append(name)
                    else:
                        analysis['modified'].append({
                            'name': name,
                            'similarity': similarity
                        })
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze section changes: {str(e)}")
            return {}

    def _identify_risk_factors(self, content: str) -> List[Dict[str, Any]]:
        """Identify potential risk factors in content"""
        risk_factors = []
        try:
            # Add risk identification logic here
            # This is a placeholder for actual risk analysis
            return risk_factors
        except Exception as e:
            self.logger.error(f"Failed to identify risk factors: {str(e)}")
            return risk_factors

    def _version_to_metadata(self, version: ContractVersion) -> Dict[str, Any]:
        """Convert version to metadata"""
        return {
            'version_id': version.version_id,
            'version_number': version.version_number,
            'timestamp': version.timestamp,
            'author': version.author,
            'changes': json.dumps(version.changes),
            'comments': version.comments,
            'status': version.status,
            'previous_version': version.previous_version,
            'sections': json.dumps([{
                'name': s.name,
                'order': s.order,
                'metadata': s.metadata
            } for s in (version.sections or [])])
        }

    def _metadata_to_version(
        self,
        metadata: Dict[str, Any],
        content: str
    ) -> ContractVersion:
        """Convert metadata to version"""
        sections = json.loads(metadata.get('sections', '[]'))
        section_objects = self._extract_sections(content)
        
        for section, section_meta in zip(section_objects, sections):
            section.metadata = section_meta['metadata']
        
        return ContractVersion(
            version_id=metadata['version_id'],
            content=content,
            version_number=metadata['version_number'],
            timestamp=metadata['timestamp'],
            author=metadata['author'],
            changes=json.loads(metadata['changes']),
            comments=metadata['comments'],
            status=metadata['status'],
            previous_version=metadata.get('previous_version'),
            sections=section_objects
        )