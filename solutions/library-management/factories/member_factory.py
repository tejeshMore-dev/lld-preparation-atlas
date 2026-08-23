from models.member import Member
from models.enum import AccountStatus, MemberType
from models.student_member import StudentMember
from models.faculty_member import FacultyMember


class MemberFactory:
    @staticmethod
    def create_member(
        account_id: str,
        name: str,
        email: str,
        member_type: MemberType,
        phone: str = "",
        account_status: AccountStatus = AccountStatus.ACTIVE,
    ) -> Member:
        member_fields = {
            "account_id": account_id,
            "name": name,
            "email": email,
            "phone": phone,
            "account_status": account_status,
            "member_type": member_type,
        }

        if member_type == MemberType.STUDENT:
            return StudentMember(
                **member_fields,
            )
        if member_type == MemberType.FACULTY:
            return FacultyMember(
                **member_fields,
            )

        raise ValueError(f"Unsupported member type: {member_type}")
